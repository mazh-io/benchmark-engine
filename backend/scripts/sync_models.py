#!/usr/bin/env python3
"""
Manual Model Sync Script

Manually trigger the model sync process that the Vercel cron runs weekly.
Use this for testing or immediate syncs.

Usage:
    python scripts/sync_models.py
    python scripts/sync_models.py --show-stats
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.provider_service import sync_models_to_database
from database.db_connector import get_db_client


def show_model_stats():
    """Display statistics about models in database."""
    db = get_db_client()
    
    print("\n" + "="*80)
    print(" DATABASE MODEL STATISTICS")
    print("="*80 + "\n")
    
    # Get all models
    all_models = db.get_all_models()
    if not all_models:
        print("No models found in database.")
        return
    
    # Get active models
    active_models = db.get_active_models()
    active_count = len(active_models) if active_models else 0
    
    # Group by provider
    by_provider = {}
    for model in all_models:
        provider_name = model.get("providers", {}).get("name", "unknown")
        if provider_name not in by_provider:
            by_provider[provider_name] = {"total": 0, "active": 0}
        
        by_provider[provider_name]["total"] += 1
        if model.get("active"):
            by_provider[provider_name]["active"] += 1
    
    # Print overall stats
    print(f"Total Models: {len(all_models)}")
    print(f"Active Models (in benchmarks): {active_count}")
    print(f"Inactive Models: {len(all_models) - active_count}")
    
    # Print per-provider stats
    print("\n" + "-"*80)
    print(f"{'Provider':<20} {'Total':<10} {'Active':<10} {'Inactive':<10}")
    print("-"*80)
    
    for provider in sorted(by_provider.keys()):
        stats = by_provider[provider]
        inactive = stats["total"] - stats["active"]
        print(f"{provider:<20} {stats['total']:<10} {stats['active']:<10} {inactive:<10}")
    
    print("-"*80)


def main():
    parser = argparse.ArgumentParser(
        description="Manually sync models to database"
    )
    parser.add_argument(
        "--show-stats",
        action="store_true",
        help="Show database statistics after sync"
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print(" SYNCING MODELS TO DATABASE")
    print("="*80 + "\n")
    
    # Run sync
    result = sync_models_to_database()
    
    # Print results
    print("\n" + "="*80)
    
    if result["success"]:
        print(" ✅ SYNC COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        print(f"Providers synced: {result['providers_synced']}")
        print(f"Models discovered: {result['models_discovered']}")
        print(f"Models activated: {result['models_activated']}")
    else:
        print(" ❌ SYNC FAILED WITH ERRORS")
        print("="*80 + "\n")
        for error in result["errors"]:
            print(f"  - {error}")
        sys.exit(1)
    
    # Show stats if requested
    if args.show_stats:
        show_model_stats()
    
    print("\n" + "="*80)
    print("\nℹ️  Models are now in the database!")
    print("   - Active=true: Models used in benchmarks")
    print("   - Active=false: Available but not benchmarked")


if __name__ == "__main__":
    main()
