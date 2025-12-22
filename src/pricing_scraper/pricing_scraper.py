import re
import requests
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

from database.supabase_client import get_or_create_provider, get_or_create_model, save_price, get_last_price_timestamp
from utils.constants import PROVIDER_CONFIG
from utils.env_helper import get_env


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []
        self._skip_depth = 0  

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1
        if tag in ("br", "p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5"):
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in ("p", "div", "tr", "li"):
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        s = data.strip()
        if s:
            self._chunks.append(s)

    def text(self) -> str:
        return "\n".join(self._chunks)


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    raw = parser.text()
    raw = re.sub(r"[ \t\r]+", " ", raw)
    raw = re.sub(r"\n{2,}", "\n", raw)
    return raw.strip()


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 40) -> requests.Response:
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


# -------------------------
# Provider fetchers
# -------------------------
def fetch_openrouter_prices() -> List[Dict[str, Any]]:
    """
    OpenRouter public pricing endpoint:
    returns items like {"id": "...", "input_cost_per_million": 0.15, "output_cost_per_million": 0.60, ...}
    """
    url = PROVIDER_CONFIG["openrouter"]["pricing_url"]
    data = _get(url).json()
    out: List[Dict[str, Any]] = []

    for entry in data.get("data", []) or []:
        model_id = entry.get("id")
        inp = entry.get("input_cost_per_million")
        outp = entry.get("output_cost_per_million")

        if not model_id or inp is None or outp is None:
            continue

        out.append(
            {
                "provider_key": "openrouter",
                "provider_name": PROVIDER_CONFIG["openrouter"]["display_name"],
                "model_name": str(model_id),
                "input_per_m": float(inp),
                "output_per_m": float(outp),
                "context_window": entry.get("context_length"),
            }
        )
    return out


def fetch_together_prices() -> List[Dict[str, Any]]:
    """
    Together: GET /v1/models (requires Bearer token)
    Response items contain `pricing: { input, output, ... }` and `context_length`.
    """
    api_key =  get_env("TOGETHER_API_KEY")
    if not api_key:
        print("[together] Skipping (missing TOGETHER_API_KEY).")
        return []

    url = PROVIDER_CONFIG["together"]["models_url"]
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    data = _get(url, headers=headers).json()

    # The API commonly returns a list directly; handle both list/dict cases.
    models = data if isinstance(data, list) else data.get("data") or data.get("models") or []

    out: List[Dict[str, Any]] = []
    for m in models:
        model_id = m.get("id")
        pricing = m.get("pricing") or {}
        inp = pricing.get("input")
        outp = pricing.get("output")
        ctx = m.get("context_length")

        if not model_id or inp is None or outp is None:
            continue

        # Many models may have 0 pricing (free). Keep or skip based on preference:
        if float(inp) == 0.0 and float(outp) == 0.0:
            continue

        out.append(
            {
                "provider_key": "together",
                "provider_name": PROVIDER_CONFIG["together"]["display_name"],
                "model_name": str(model_id),
                "input_per_m": float(inp),
                "output_per_m": float(outp),
                "context_window": int(ctx) if isinstance(ctx, (int, float)) else None,
            }
        )
    return out


def fetch_openai_standard_prices() -> List[Dict[str, Any]]:
    """
    Scrapes OpenAI docs pricing table (Text tokens -> Standard).
    We store only input/output per 1M tokens.
    """
    url = PROVIDER_CONFIG["openai"]["pricing_url"]
    html = _get(url).text
    text = _html_to_text(html)

    # Isolate: "Text tokens" section, then take "Standard" sub-section until "Priority"
    text_tokens_start = text.find("Text tokens")
    if text_tokens_start == -1:
        raise RuntimeError("[openai] Could not locate 'Text tokens' section.")

    image_tokens_start = text.find("Image tokens", text_tokens_start)
    segment = text[text_tokens_start : (image_tokens_start if image_tokens_start != -1 else None)]

    standard_start = segment.find("Standard")
    if standard_start == -1:
        raise RuntimeError("[openai] Could not locate 'Standard' pricing section in Text tokens.")

    priority_start = segment.find("Priority", standard_start)
    standard_segment = segment[standard_start : (priority_start if priority_start != -1 else None)]

    # Collapse whitespace; the docs often render as: model$input$cached$output
    collapsed = re.sub(r"\s+", "", standard_segment)

    # model $input $cached $output
    # cached or output may be '-' for some entries; we only keep rows where output is numeric.
    pattern = re.compile(
        r"(?P<model>[A-Za-z0-9][A-Za-z0-9\.\-_]+)"
        r"\$(?P<input>\d+(?:\.\d+)?)"
        r"\$(?P<cached>\d+(?:\.\d+)?|-)"
        r"\$(?P<output>\d+(?:\.\d+)?|-)"
    )

    out: List[Dict[str, Any]] = []
    for m in pattern.finditer(collapsed):
        model_name = m.group("model")
        inp = m.group("input")
        outp = m.group("output")
        if outp == "-":
            continue

        out.append(
            {
                "provider_key": "openai",
                "provider_name": PROVIDER_CONFIG["openai"]["display_name"],
                "model_name": model_name,
                "input_per_m": float(inp),
                "output_per_m": float(outp),
                "context_window": None,
            }
        )

    if not out:
        raise RuntimeError("[openai] Parsed 0 rows (page structure likely changed).")
    return out


def fetch_groq_llm_prices() -> List[Dict[str, Any]]:
    """
    Scrapes Groq pricing page, LLM section only (Input/Output Token Price per million).
    """
    url = PROVIDER_CONFIG["groq"]["pricing_url"]
    html = _get(url).text
    text = _html_to_text(html)

    start = text.find("Large Language Models")
    if start == -1:
        raise RuntimeError("[groq] Could not locate 'Large Language Models' section.")

    end = text.find("Text-to-Speech Models", start)
    section = text[start : (end if end != -1 else None)]

    out: List[Dict[str, Any]] = []

    # Split by repeated "AI Model" blocks.
    chunks = section.split("AI Model")
    for ch in chunks:
        ch = ch.strip()
        if not ch:
            continue

        # First line in chunk is the model name (usually)
        model_name = ch.split("\n", 1)[0].strip()
        if not model_name or model_name.lower().startswith(("current speed", "input token price", "output token price")):
            continue

        inp_m = re.search(r"Input Token Price.*?\$(\d+(?:\.\d+)?)", ch, flags=re.IGNORECASE | re.DOTALL)
        out_m = re.search(r"Output Token Price.*?\$(\d+(?:\.\d+)?)", ch, flags=re.IGNORECASE | re.DOTALL)
        if not inp_m or not out_m:
            continue

        out.append(
            {
                "provider_key": "groq",
                "provider_name": PROVIDER_CONFIG["groq"]["display_name"],
                "model_name": model_name,
                "input_per_m": float(inp_m.group(1)),
                "output_per_m": float(out_m.group(1)),
                "context_window": None,
            }
        )

    if not out:
        raise RuntimeError("[groq] Parsed 0 LLM rows (page structure likely changed).")
    return out


# -------------------------
# DB save
# -------------------------
def save_prices_to_db(rows: List[Dict[str, Any]]) -> None:
    """Save prices to database only if 24 hours have passed since last update."""
    inserted_count = 0
    skipped_count = 0
    
    for r in rows:
        provider_key = r["provider_key"]
        provider_name = r["provider_name"]
        base_url = PROVIDER_CONFIG[provider_key]["base_url"]

        model_name = r["model_name"]
        input_per_m = r["input_per_m"]
        output_per_m = r["output_per_m"]

        if not model_name or input_per_m is None or output_per_m is None:
            continue

        provider_id = get_or_create_provider(provider_name, base_url, None)
        if not provider_id:
            continue

        model_id = get_or_create_model(model_name, provider_id)
        if not model_id:
            continue

        # Check if 24 hours have passed since last price update
        last_timestamp = get_last_price_timestamp(provider_id, model_id)
        if last_timestamp:
            # Parse timestamp (handle both ISO format with/without timezone)
            if isinstance(last_timestamp, str):
                # Remove timezone info if present for comparison
                if last_timestamp.endswith('Z'):
                    last_timestamp = last_timestamp[:-1]
                if '+' in last_timestamp:
                    last_timestamp = last_timestamp.split('+')[0]
                last_dt = datetime.fromisoformat(last_timestamp.replace('Z', ''))
            else:
                last_dt = last_timestamp
            
            # Make sure last_dt is timezone-aware
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            time_diff = now - last_dt
            
            if time_diff < timedelta(hours=24):
                skipped_count += 1
                continue
        
        # Insert new price record (no updates, only inserts)
        save_price(provider_id, model_id, float(input_per_m), float(output_per_m))
        inserted_count += 1
    
    print(f"[save_prices] Inserted: {inserted_count}, Skipped (within 24h): {skipped_count}")


# -------------------------
# Runner
# -------------------------
def run_pricing_scraper(providers: Optional[List[str]] = None) -> None:
    """
    providers: e.g. ["openai","groq","together","openrouter"] (default: all)
    """
    providers = providers or ["openai", "groq", "together", "openrouter"]

    print(f"[{_utc_iso()}] Starting pricing scraper for: {providers}")

    all_rows: List[Dict[str, Any]] = []

    for p in providers:
        try:
            if p == "openai":
                rows = fetch_openai_standard_prices()
            elif p == "groq":
                rows = fetch_groq_llm_prices()
            elif p == "together":
                rows = fetch_together_prices()
            elif p == "openrouter":
                rows = fetch_openrouter_prices()
            else:
                print(f"[warn] Unknown provider key: {p} (skipping)")
                continue

            print(f"[{p}] fetched {len(rows)} rows")
            all_rows.extend(rows)
        except Exception as e:
            print(f"[{p}] ERROR: {e}")

    save_prices_to_db(all_rows)
    print(f"[{_utc_iso()}] Done. Saved {len(all_rows)} rows.")


if __name__ == "__main__":
    run_pricing_scraper()