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
from database.supabase_client import get_or_create_provider, get_or_create_model, save_price

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
    Execute a single benchmark run with a timestamp in the name.
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    run_name = f"cron-run-{timestamp}"
    
    try:
        log_info(f"Starting single benchmark run: {run_name}", {"triggered_by": "cron-job"})
        
        # Populate prices table before running benchmark
        print("Populating prices table...")
        success_count, error_count = populate_prices_table()
        print(f"Prices table populated: {success_count} successful, {error_count} errors\n")
        
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

