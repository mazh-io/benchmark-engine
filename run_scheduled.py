#!/usr/bin/env python3
"""
Scheduled benchmark runner - Runs the benchmark every 15 minutes for 4 hours.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add src folder to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from benchmarking.benchmark_runner import run_benchmark
from utils.logger import log_info, log_error

# Configuration
INTERVAL_MINUTES = 15  # Every 15 min
DURATION_HOURS = 4     # For 4 hours
TOTAL_RUNS = (DURATION_HOURS * 60) // INTERVAL_MINUTES  # 16 runs

def main():
    """
    Runs the benchmark every 15 minutes for 4 hours.
    """
    print("=" * 60)
    print("Scheduled Benchmark Runner")
    print("=" * 60)
    print(f"Interval: {INTERVAL_MINUTES} minutes")
    print(f"Duration: {DURATION_HOURS} hours")
    print(f"Total runs: {TOTAL_RUNS}")
    print("=" * 60)
    print()
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=DURATION_HOURS)
    
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Will run until: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    log_info("Scheduled benchmark runner started", {
        "interval_minutes": INTERVAL_MINUTES,
        "duration_hours": DURATION_HOURS,
        "total_runs": TOTAL_RUNS
    })
    
    run_count = 0
    
    while datetime.now() < end_time:
        run_count += 1
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"Run #{run_count}/{TOTAL_RUNS} - {current_time}")
        print(f"{'='*60}\n")
        
        # Execute benchmark
        try:
            run_benchmark(
                run_name=f"scheduled-run-{run_count}",
                triggered_by="scheduled-runner"
            )
        except Exception as e:
            log_error(f"Error in scheduled run #{run_count}: {str(e)}", {"run_count": run_count})
            print(f"❌ Error in run #{run_count}: {e}")
            # Continue to next run even if this one failed
        
        # If we haven't reached the end time, wait 15 minutes
        if datetime.now() < end_time:
            wait_seconds = INTERVAL_MINUTES * 60
            print(f"\nWaiting {INTERVAL_MINUTES} minutes until next run...")
            next_run_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=INTERVAL_MINUTES)
            print(f"Next run at: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(wait_seconds)
    
    print("\n" + "=" * 60)
    print("Scheduled benchmark completed!")
    print(f"Total runs executed: {run_count}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()

