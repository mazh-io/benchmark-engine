import sys
import os

# Shto src folder ne PYTHONPATH qe Python te gjeje modulet
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from benchmarking.benchmark_runner import run_benchmark


def main():
    """
    Entry point i aplikacionit.
    Ekzekuton benchmark-in per krejt provider-at.
    """
    print("=" * 60)
    print("Benchmark Engine – MVP")
    print("=" * 60)
    print()

    # Thirr funksionin kryesor qe e ekzekuton benchmark-in
    run_benchmark(
        run_name="mvp-validation-run",  # Emri i run-it
        triggered_by="system"           # Kush e ka nis ne system
    )

if __name__ == "__main__":
    main()
