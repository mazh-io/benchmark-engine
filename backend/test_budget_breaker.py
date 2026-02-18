"""
Test Budget Circuit Breaker with Real Database

This script demonstrates the budget check using actual spending data.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from database.db_connector import get_db_client
from utils.budget_breaker import BudgetCircuitBreaker


def main():
    print("=" * 80)
    print("BUDGET CIRCUIT BREAKER - LIVE TEST")
    print("=" * 80)
    
    # Get database client
    print("\n📡 Connecting to database...")
    db = get_db_client()
    
    # Initialize circuit breaker with default budget ($15)
    print("💰 Initializing budget check (cap: $15.00)...\n")
    breaker = BudgetCircuitBreaker(budget_cap_usd=15.0)
    
    # Check spending for different time windows
    time_windows = [1, 6, 12, 24, 48]
    
    for hours in time_windows:
        print(f"\n{'='*80}")
        print(f"TIME WINDOW: Last {hours} hour(s)")
        print("="*80)
        
        result = breaker.check_budget(db, hours=hours)
        
        print(f"\n📊 Spending Report:")
        print(f"   Current spend: ${result['current_spend']:.4f}")
        print(f"   Budget cap: ${result['budget_cap']:.2f}")
        print(f"   Remaining: ${result['remaining_budget']:.4f}")
        print(f"   Usage: {result['percent_used']:.1f}%")
        
        if result['should_abort']:
            print(f"\n🚨 Status: BUDGET EXCEEDED")
            print(f"   Over budget by: ${-result['remaining_budget']:.4f}")
            print(f"   Action: ⛔ WOULD ABORT EXECUTION")
        else:
            print(f"\n✅ Status: Within Budget")
            print(f"   Action: ✓ Proceed with benchmark")
    
    # Final summary
    print(f"\n{'='*80}")
    print("CONFIGURATION")
    print("="*80)
    print(f"\n📝 Budget Settings:")
    print(f"   Default cap: $15.00")
    print(f"   Environment variable: BENCHMARK_BUDGET_CAP")
    print(f"   Current setting: ${breaker.budget_cap:.2f}")
    
    print(f"\n🔧 To change budget cap:")
    print(f"   export BENCHMARK_BUDGET_CAP=25.0  # Set to $25")
    print(f"   export BENCHMARK_BUDGET_CAP=50.0  # Set to $50")
    
    print(f"\n📚 Usage in code:")
    print(f"   from utils.budget_breaker import BudgetCircuitBreaker")
    print(f"   breaker = BudgetCircuitBreaker()")
    print(f"   result = breaker.check_budget(db)")
    print(f"   if result['should_abort']:")
    print(f"       print('Budget exceeded!')")
    print(f"       return  # Abort execution")
    
    print("\n" + "="*80)
    print("✅ Budget check complete!")
    print("="*80)


if __name__ == "__main__":
    main()
