"""
Vercel Serverless Function for running benchmarks.
This endpoint can be triggered by Vercel Cron or manually via HTTP.
"""

import sys
import os

# Add src folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchmarking.benchmark_runner import run_benchmark


def handler(request):
    """
    Vercel serverless function handler.
    Triggers a single benchmark run.
    """
    try:
        # Run the benchmark
        run_benchmark(
            run_name="vercel-cron-run",
            triggered_by="vercel-cron"
        )
        
        return {
            "statusCode": 200,
            "body": "Benchmark completed successfully"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Benchmark failed: {str(e)}"
        }
