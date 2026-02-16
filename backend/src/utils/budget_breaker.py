"""
Budget Circuit Breaker

Prevents runaway costs by checking spending before benchmark runs.
Aborts execution if spending exceeds configured daily budget.

This is a safety net for automated cron jobs to prevent infinite loops
from draining your API budget.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class BudgetCircuitBreaker:
    """
    Circuit breaker to prevent excessive spending on API calls.
    
    Checks total spending in the last 24 hours and aborts if budget exceeded.
    """
    
    def __init__(self, budget_cap_usd: Optional[float] = None):
        """
        Initialize circuit breaker with budget cap.
        
        Args:
            budget_cap_usd: Maximum allowed spending in USD per 24 hours.
                           If None, reads from BENCHMARK_BUDGET_CAP env var.
                           Defaults to $15 if not set.
        """
        if budget_cap_usd is not None:
            self.budget_cap = budget_cap_usd
        else:
            # Read from environment variable or use default
            self.budget_cap = float(os.getenv('BENCHMARK_BUDGET_CAP', '15.0'))
        
        logger.info(f"Budget circuit breaker initialized: ${self.budget_cap:.2f} per 24h")
    
    def check_budget(self, db, hours: int = 24) -> Dict[str, any]:
        """
        Check if current spending is within budget.
        
        Args:
            db: Database client instance
            hours: Time window to check (default: 24 hours)
            
        Returns:
            Dict with:
            - within_budget: Boolean
            - current_spend: Current spending in time window
            - budget_cap: Configured budget cap
            - remaining_budget: Remaining budget
            - time_window_hours: Time window checked
            - should_abort: Whether to abort execution
        """
        try:
            # Get spending in last N hours
            current_spend = self._get_recent_spending(db, hours)
            
            remaining = self.budget_cap - current_spend
            within_budget = current_spend < self.budget_cap
            
            result = {
                "within_budget": within_budget,
                "current_spend": round(current_spend, 4),
                "budget_cap": self.budget_cap,
                "remaining_budget": round(remaining, 4),
                "time_window_hours": hours,
                "should_abort": not within_budget,
                "percent_used": round((current_spend / self.budget_cap * 100), 1) if self.budget_cap > 0 else 0
            }
            
            # Log status
            if within_budget:
                logger.info(
                    f"Budget check passed: ${current_spend:.2f} / ${self.budget_cap:.2f} "
                    f"({result['percent_used']}% used)"
                )
            else:
                logger.error(
                    f"🚨 BUDGET EXCEEDED: ${current_spend:.2f} / ${self.budget_cap:.2f} "
                    f"({result['percent_used']}% used)"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking budget: {e}")
            # On error, allow execution (fail open to avoid blocking legitimate runs)
            return {
                "within_budget": True,
                "current_spend": 0,
                "budget_cap": self.budget_cap,
                "remaining_budget": self.budget_cap,
                "time_window_hours": hours,
                "should_abort": False,
                "error": str(e)
            }
    
    def _get_recent_spending(self, db, hours: int) -> float:
        """Get total spending in the last N hours."""
        try:
            if hasattr(db, 'supabase'):
                # Supabase client
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                response = db.supabase.table("benchmark_results").select(
                    "cost_usd"
                ).gte("created_at", cutoff_time.isoformat()).execute()
                
                total = sum(row.get('cost_usd', 0) for row in response.data if row.get('cost_usd'))
                return total
                
            else:
                # Local PostgreSQL client
                conn = db._get_connection()
                cur = conn.cursor()
                
                cur.execute("""
                    SELECT COALESCE(SUM(cost_usd), 0) as total
                    FROM benchmark_results
                    WHERE created_at >= NOW() - INTERVAL '%s hours'
                """, (hours,))
                
                result = cur.fetchone()
                total = float(result[0]) if result else 0.0
                
                cur.close()
                conn.close()
                
                return total
                
        except Exception as e:
            logger.error(f"Error fetching recent spending: {e}")
            return 0.0
    
    def enforce_budget(self, db, hours: int = 24) -> bool:
        """
        Check budget and raise exception if exceeded.
        
        Args:
            db: Database client instance
            hours: Time window to check
            
        Returns:
            True if within budget
            
        Raises:
            BudgetExceededException if budget exceeded
        """
        result = self.check_budget(db, hours)
        
        if result["should_abort"]:
            raise BudgetExceededException(
                f"Budget exceeded: ${result['current_spend']:.2f} / ${result['budget_cap']:.2f} "
                f"in last {hours} hours"
            )
        
        return True
    
    def get_status_message(self, db, hours: int = 24) -> str:
        """Get a human-readable budget status message."""
        result = self.check_budget(db, hours)
        
        if result["should_abort"]:
            return (
                f"🚨 BUDGET EXCEEDED\n"
                f"   Current spend: ${result['current_spend']:.2f}\n"
                f"   Budget cap: ${result['budget_cap']:.2f}\n"
                f"   Over budget by: ${-result['remaining_budget']:.2f}\n"
                f"   Time window: {hours} hours\n"
                f"   ⚠️  Aborting to prevent overspending!"
            )
        else:
            return (
                f"💰 Budget Status: OK\n"
                f"   Current spend: ${result['current_spend']:.2f}\n"
                f"   Budget cap: ${result['budget_cap']:.2f}\n"
                f"   Remaining: ${result['remaining_budget']:.2f}\n"
                f"   Used: {result['percent_used']}%\n"
                f"   Time window: {hours} hours"
            )


class BudgetExceededException(Exception):
    """Raised when budget is exceeded."""
    pass


def check_budget_before_run(db, budget_cap: Optional[float] = None) -> bool:
    """
    Convenience function to check budget before starting a benchmark run.
    
    Args:
        db: Database client instance
        budget_cap: Optional budget cap override (uses env var if None)
        
    Returns:
        True if within budget
        
    Raises:
        BudgetExceededException if budget exceeded
        
    Example:
        >>> from database.db_connector import get_db_client
        >>> db = get_db_client()
        >>> check_budget_before_run(db)  # Raises exception if over budget
        True
    """
    breaker = BudgetCircuitBreaker(budget_cap)
    return breaker.enforce_budget(db)


# Example usage
if __name__ == "__main__":
    print("Budget Circuit Breaker - Test Mode")
    print("=" * 80)
    
    # Test with mock spending data
    class MockDB:
        """Mock database for testing."""
        def _get_connection(self):
            return None
    
    # Simulate different scenarios
    print("\nScenario 1: Well within budget")
    print("-" * 80)
    breaker = BudgetCircuitBreaker(budget_cap_usd=15.0)
    
    # Mock spending check
    result = {
        "within_budget": True,
        "current_spend": 5.25,
        "budget_cap": 15.0,
        "remaining_budget": 9.75,
        "time_window_hours": 24,
        "should_abort": False,
        "percent_used": 35.0
    }
    
    print(f"Current spend: ${result['current_spend']:.2f}")
    print(f"Budget cap: ${result['budget_cap']:.2f}")
    print(f"Status: {'✅ OK' if result['within_budget'] else '🚨 EXCEEDED'}")
    print(f"Remaining: ${result['remaining_budget']:.2f}")
    print(f"Usage: {result['percent_used']}%")
    
    print("\nScenario 2: Budget exceeded")
    print("-" * 80)
    result = {
        "within_budget": False,
        "current_spend": 18.50,
        "budget_cap": 15.0,
        "remaining_budget": -3.50,
        "time_window_hours": 24,
        "should_abort": True,
        "percent_used": 123.3
    }
    
    print(f"Current spend: ${result['current_spend']:.2f}")
    print(f"Budget cap: ${result['budget_cap']:.2f}")
    print(f"Status: {'✅ OK' if result['within_budget'] else '🚨 EXCEEDED'}")
    print(f"Over budget by: ${-result['remaining_budget']:.2f}")
    print(f"Usage: {result['percent_used']}%")
    print(f"Action: {'Continue' if not result['should_abort'] else '⛔ ABORT EXECUTION'}")
    
    print("\n" + "=" * 80)
    print("Configuration:")
    print(f"  Environment variable: BENCHMARK_BUDGET_CAP")
    print(f"  Default value: $15.00")
    print(f"  Current setting: ${breaker.budget_cap:.2f}")
