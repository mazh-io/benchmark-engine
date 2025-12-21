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
from utils.logger import log_info, log_error

def main():
    """
    Execute a single benchmark run with a timestamp in the name.
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    run_name = f"cron-run-{timestamp}"
    
    try:
        log_info(f"Starting single benchmark run: {run_name}", {"triggered_by": "cron-job"})
        
        run_benchmark(
            run_name=run_name,
            triggered_by="cron-job"
        )
        
        log_info(f"Completed single benchmark run: {run_name}")
        
    except Exception as e:
        log_error(f"Error in single benchmark run: {str(e)}", {"run_name": run_name})
        raise

if __name__ == "__main__":
    main()

