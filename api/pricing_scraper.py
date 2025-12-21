import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pricing_scraper.pricing_scraper import run_pricing_scraper


def default(request):
    try:
        run_pricing_scraper()
        return ("Pricing scraper completed successfully.", 200)
    except Exception as e:
        return (f"Pricing scraper failed: {str(e)}", 500)
