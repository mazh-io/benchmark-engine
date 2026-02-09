import sys
import os
import argparse

# Add src folder to PYTHONPATH so Python can find modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    """
    Entry point for the Benchmark Engine.

    Modes:
        serve   → Start the FastAPI server (default)
        bench   → Run a one-off benchmark from the CLI
    """
    parser = argparse.ArgumentParser(description="Benchmark Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- serve ---
    serve_parser = subparsers.add_parser("serve", help="Start the FastAPI server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    serve_parser.add_argument("--no-scheduler", action="store_true", help="Disable the built-in cron scheduler")

    # --- bench (legacy CLI mode) ---
    bench_parser = subparsers.add_parser("bench", help="Run a one-off benchmark (CLI)")
    bench_parser.add_argument("--run-name", default="cli-run", help="Name of the run")
    bench_parser.add_argument("--triggered-by", default="cli", help="Who triggered the run")
    bench_parser.add_argument("--providers", nargs="*", default=None, help="Provider filter (e.g., openai groq)")

    args = parser.parse_args()

    # Default to 'serve' when no subcommand is given
    if args.command is None or args.command == "serve":
        import uvicorn

        # Optionally disable the scheduler via env var
        if hasattr(args, "no_scheduler") and args.no_scheduler:
            os.environ["DISABLE_SCHEDULER"] = "1"

        host = getattr(args, "host", "0.0.0.0")
        port = getattr(args, "port", 8000)
        reload = getattr(args, "reload", False)

        print("=" * 60)
        print("Benchmark Engine – FastAPI")
        print(f"Starting on http://{host}:{port}")
        print(f"API docs at  http://{host}:{port}/docs")
        print("=" * 60)

        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
        )

    elif args.command == "bench":
        from benchmarking.benchmark_runner import run_benchmark

        print("=" * 60)
        print("Benchmark Engine – CLI Run")
        print("=" * 60)
        print()

        run_benchmark(
            run_name=args.run_name,
            triggered_by=args.triggered_by,
            provider_filter=args.providers,
        )


if __name__ == "__main__":
    main()
