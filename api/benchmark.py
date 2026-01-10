"""
Vercel Serverless Function for running benchmarks.
Uses queue-based processing to avoid timeout issues.
Each invocation processes a batch from the queue.
"""

import sys
import os
from http.server import BaseHTTPRequestHandler
import json

# Add src folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchmarking.queue_benchmark_runner import run_benchmark_batch, init_benchmark_queue
from database.db_connector import get_db_client


class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless function handler.
    
    Query params:
    - action=init: Initialize new run and populate queue
    - action=process (default): Process batch from queue
    """
    
    def do_GET(self):
        try:
            # Parse query params
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            action = params.get('action', ['process'])[0]
            
            if action == 'init':
                # Initialize new benchmark run
                run_id = init_benchmark_queue(
                    run_name="vercel-queue-run",
                    triggered_by="vercel-cron"
                )
                
                if run_id:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "success",
                        "message": "Benchmark queue initialized",
                        "run_id": run_id
                    }).encode())
                else:
                    raise Exception("Failed to initialize queue")
            
            else:
                # Process batch from queue (default action)
                result = run_benchmark_batch(batch_size=10)
                
                # Get queue stats if we processed items
                db = get_db_client()
                queue_stats = None
                if result.get("processed", 0) > 0:
                    # Try to get stats from first queue item's run_id
                    # In practice, all items in a batch should have same run_id
                    pending_items = db.get_pending_queue_items(limit=1)
                    if pending_items and len(pending_items) > 0:
                        run_id = str(pending_items[0]['run_id'])
                        queue_stats = db.get_queue_stats(run_id)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Batch processed",
                    "result": result,
                    "queue_stats": queue_stats
                }).encode())
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in benchmark handler: {error_details}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e),
                "details": error_details
            }).encode())
