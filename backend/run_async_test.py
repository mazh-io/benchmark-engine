#!/usr/bin/env python3
"""
Quick local test for the async benchmark runner.

Usage:
    cd backend
    source .venv/bin/activate

    # Test with a single provider:
    python run_async_test.py --providers openai

    # Test with a few providers (concurrent):
    python run_async_test.py --providers openai anthropic groq

    # Test all providers:
    python run_async_test.py

    # Control concurrency:
    python run_async_test.py --providers openai groq anthropic --concurrency 3
"""

import sys
import os
import argparse

# Add src/ to PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load .env
from dotenv import load_dotenv
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Test async benchmark runner locally")
    parser.add_argument(
        "--providers", nargs="*", default=None,
        help="Provider filter, e.g. --providers openai anthropic groq"
    )
    parser.add_argument(
        "--run-name", default="async-local-test",
        help="Run name (default: async-local-test)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10,
        help="Max concurrent API calls (default: 10)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Async Benchmark Runner — Local Test")
    print("=" * 60)

    if args.providers:
        print(f"   Providers: {', '.join(args.providers)}")
    else:
        print("   Providers: ALL")
    print(f"   Concurrency: {args.concurrency}")
    print()

    from benchmarking.async_benchmark_runner import run_async_benchmark

    run_async_benchmark(
        run_name=args.run_name,
        triggered_by="local-test",
        provider_filter=args.providers,
        max_concurrent=args.concurrency,
    )


if __name__ == "__main__":
    main()
