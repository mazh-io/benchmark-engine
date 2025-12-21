import sys
import os
from http.server import BaseHTTPRequestHandler
import json

# Add src folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pricing_scraper.pricing_scraper import run_pricing_scraper



class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless function handler.
    Triggers a single benchmark run.
    """
    
    def do_GET(self):
        try:
            # Run pricing scraper
            run_pricing_scraper()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Benchmark completed successfully"}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())


