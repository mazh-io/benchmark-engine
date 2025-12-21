import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pricing_scraper.pricing_scraper import run_pricing_scraper


def handler(request):
    try:
        run_pricing_scraper()
        return {
            "statusCode": 200,
            "body": "Pricing scraper completed successfully."
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Pricing scraper failed: {str(e)}"
        }
