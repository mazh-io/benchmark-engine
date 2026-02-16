import sys
import os

# Add src folder to PYTHONPATH so Python can find modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from pricing_scraper.pricing_scraper import run_pricing_scraper


def main():
    """
    Entry point for pricing scraper.
    Scrapes pricing data from all providers and saves to database.
    """
    print("=" * 60)
    print("Pricing Scraper – Updating Database")
    print("=" * 60)
    print()

    # Run the pricing scraper for all providers
    run_pricing_scraper()

if __name__ == "__main__":
    main()
