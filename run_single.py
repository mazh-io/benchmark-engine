#!/usr/bin/env python3
"""
Single benchmark run - used by cron job for a single execution.
"""

import sys
import os
from datetime import datetime

# Add src folder to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from benchmarking.benchmark_runner import run_benchmark

def main():
    """
    Execute a single benchmark run with a timestamp in the name.
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    run_benchmark(
        run_name=f"cron-run-{timestamp}",
        triggered_by="cron-job"
    )

if __name__ == "__main__":
    main()

