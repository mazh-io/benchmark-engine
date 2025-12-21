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
from database.supabase_client import get_or_create_provider, get_or_create_model, save_price

# Configuration
INTERVAL_MINUTES = 15  # Every 15 min
DURATION_HOURS = 4     # For 4 hours
TOTAL_RUNS = (DURATION_HOURS * 60) // INTERVAL_MINUTES  # 16 runs

# Pricing data from provider files
PRICING_DATA = [
    # OpenAI
    ("OpenAI", "gpt-4o-mini", 0.15, 0.60),
    ("OpenAI", "gpt-4o", 2.50, 10.00),
    ("OpenAI", "gpt-4-turbo", 10.00, 30.00),
    ("OpenAI", "gpt-3.5-turbo", 0.50, 1.50),
    # Groq
    ("Groq", "llama-3.1-8b-instant", 0.05, 0.08),
    ("Groq", "llama-3.1-70b-versatile", 0.59, 0.79),
    ("Groq", "mixtral-8x7b-32768", 0.24, 0.24),
    # Together AI
    ("Together AI", "mistralai/Mixtral-8x7B-Instruct-v0.1", 0.24, 0.24),
    ("Together AI", "meta-llama/Llama-3-8b-chat-hf", 0.10, 0.10),
    ("Together AI", "meta-llama/Llama-3-70b-chat-hf", 0.59, 0.79),
    # OpenRouter
    ("OpenRouter", "openai/gpt-4o-mini", 0.15, 0.60),
]

def populate_prices_table():
    """
    Populate the prices table with current pricing data.
    """
    success_count = 0
    error_count = 0
    
    for provider_display, model_name, input_price, output_price in PRICING_DATA:
        # Get or create provider
        provider_id = get_or_create_provider(provider_display, None, None)
        if not provider_id:
            error_count += 1
            continue
        
        # Get or create model
        model_id = get_or_create_model(model_name, provider_id)
        if not model_id:
            error_count += 1
            continue
        
        # Save price
        price_id = save_price(provider_id, model_id, input_price, output_price)
        if price_id:
            success_count += 1
        else:
            error_count += 1
    
    return success_count, error_count

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
    
    # Populate prices table before starting benchmarks
    print("\nPopulating prices table...")
    success_count, error_count = populate_prices_table()
    print(f"Prices table populated: {success_count} successful, {error_count} errors\n")
    
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

