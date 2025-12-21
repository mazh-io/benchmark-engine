import requests
from datetime import datetime
from database.supabase_client import get_or_create_provider, get_or_create_model, save_price

OPENROUTER_PRICING_URL = "https://openrouter.ai/api/v1/pricing/public"


def fetch_openrouter_prices():
    resp = requests.get(OPENROUTER_PRICING_URL)
    resp.raise_for_status()
    data = resp.json()
    # Example structure: {"data": [{"id": "openai/gpt-4o-mini", "input_cost_per_million": 0.15, ...}]}
    return data.get("data", [])


def save_prices_to_db(prices):
    for entry in prices:
        model_name = entry.get("id")
        provider_name = entry.get("provider", "OpenRouter")
        input_price = entry.get("input_cost_per_million")
        output_price = entry.get("output_cost_per_million")
        timestamp = datetime.utcnow().isoformat()
        if not (model_name and input_price is not None and output_price is not None):
            continue
        provider_id = get_or_create_provider(provider_name, None, None)
        if not provider_id:
            continue
        model_id = get_or_create_model(model_name, provider_id)
        if not model_id:
            continue
        save_price(provider_id, model_id, input_price, output_price, timestamp=timestamp)


def run_pricing_scraper():
    print(f"[{datetime.utcnow().isoformat()}] Fetching OpenRouter prices...")
    prices = fetch_openrouter_prices()
    save_prices_to_db(prices)
    print(f"[{datetime.utcnow().isoformat()}] Prices updated. {len(prices)} entries.")


if __name__ == "__main__":
    run_pricing_scraper()
