"""
Vercel Serverless Function for running benchmarks.
This endpoint can be triggered by Vercel Cron or manually via HTTP.
"""

import sys
import os
from http.server import BaseHTTPRequestHandler
import json

# Add src folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchmarking.benchmark_runner import run_benchmark


class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless function handler.
    Triggers a single benchmark run.
    """
    
    def do_GET(self):
        try:
            # Run the benchmark
            run_benchmark(
                run_name="vercel-cron-run",
                triggered_by="vercel-cron"
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Benchmark completed successfully"}).encode())
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in benchmark handler: {error_details}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e), "details": error_details}).encode())
