"""
Main pricing scraper module.

Refactored to use dependency injection and abstraction layers.
Each provider has its own scraper implementing BasePricingScraper interface.

The orchestrator manages scraper execution and result aggregation.

Example:
    python -m src.pricing_scraper.pricing_scraper
    Or in Python code:
        from src.pricing_scraper.pricing_scraper import run_pricing_scraper
        run_pricing_scraper(providers=["openai","groq"])
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from database.db_connector import get_db_client
from pricing_scraper.orchestrator import PricingScraperOrchestrator
from utils.constants import PROVIDER_CONFIG


def _utc_iso() -> str:
    """Return current UTC ISO timestamp (for logs)."""
    return datetime.now(timezone.utc).isoformat()


def save_prices_to_db(rows: List[Dict[str, Any]]) -> None:
    """Save prices to database only if 24 hours have passed since last update."""
    inserted_count = 0
    skipped_count = 0
    
    # Get database client
    db = get_db_client()
    
    for r in rows:
        provider_key = r["provider_key"]
        # Use display_name from PROVIDER_CONFIG for consistency with benchmark
        provider_display_name = PROVIDER_CONFIG[provider_key].get("display_name", r["provider_name"])
        base_url = PROVIDER_CONFIG[provider_key]["base_url"]

        model_name = r["model_name"]
        input_per_m = r["input_per_m"]
        output_per_m = r["output_per_m"]

        if not model_name or input_per_m is None or output_per_m is None:
            continue

        provider_id = db.get_or_create_provider(provider_display_name, base_url, None)
        if not provider_id:
            continue

        model_id = db.get_or_create_model(model_name, provider_id)
        if not model_id:
            continue

        # Check if 24 hours have passed since last price update
        last_timestamp = db.get_last_price_timestamp(provider_id, model_id)
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
        db.save_price(provider_id, model_id, float(input_per_m), float(output_per_m))
        inserted_count += 1
    
    print(f"[save_prices] Inserted: {inserted_count}, Skipped (within 24h): {skipped_count}")


def run_pricing_scraper(providers: Optional[List[str]] = None) -> None:
    """
    Run the pricing scraper for specified providers or all providers.
    
    Args:
        providers: List of provider keys to scrape (e.g., ["openai", "groq"]).
                  If None, scrapes all configured providers.
    """
    print(f"[{_utc_iso()}] Starting pricing scraper...")
    
    orchestrator = PricingScraperOrchestrator()
    
    if providers:
        # Scrape specific providers
        all_rows: List[Dict[str, Any]] = []
        for provider_key in providers:
            try:
                rows = orchestrator.scrape_provider(provider_key)
                all_rows.extend(rows)
            except Exception as e:
                print(f"[{provider_key}] ERROR: {e}")
    else:
        # Scrape all providers
        all_rows = orchestrator.scrape_all_providers()
    
    # Save results to database
    save_prices_to_db(all_rows)
    print(f"[{_utc_iso()}] Done. Processed {len(all_rows)} total rows.")


if __name__ == "__main__":
    run_pricing_scraper()
