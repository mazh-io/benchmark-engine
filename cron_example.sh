#!/bin/bash
# Example cron job script for benchmark engine
# Usage:
# 1. Make script executable: chmod +x cron_example.sh
# 2. Add to crontab: crontab -e
# 3. Add this line for every 15 minutes:
#    */15 * * * * /path/to/benchmark-engine/cron_example.sh

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run single benchmark
python run_single.py

# Deactivate virtual environment
deactivate

