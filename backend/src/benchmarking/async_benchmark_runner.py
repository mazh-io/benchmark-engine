"""
Async Benchmark Runner

Replaces the sequential benchmark_runner.py with an asyncio-based runner
that executes all providers **concurrently** using ``asyncio.gather()``.

Key design decisions:
  • A ``Semaphore`` limits how many providers call their API at the same
    time (default 10).  This prevents hitting OS socket limits and gives
    each provider a fairer share of the network.
  • 429 rate-limited providers are collected into a *pending* list and
    retried in deferred rounds (same strategy as the sync runner) using
    ``asyncio.sleep`` instead of ``time.sleep``.
  • DB writes remain synchronous (Supabase client is sync) — they're
    fast single-row inserts and don't benefit from being async.
"""

import asyncio
from typing import Optional, List, Dict, Any, Tuple, Callable

from benchmarking.run_manager import RunManager
from database.db_connector import get_db_client

from utils.constants import BENCHMARK_PROMPT, PROVIDER_CONFIG
from utils.async_provider_service import get_async_providers
from utils.budget_breaker import BudgetCircuitBreaker


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_CONCURRENT = 10             # Max simultaneous API calls
DEFERRED_RETRY_ROUNDS = 2      # Retry rounds for rate-limited providers
DEFERRED_COOLDOWN_SECS = 30    # Seconds between retry rounds


# ======================================================================
# Helpers (sync — DB writes are cheap single-row inserts)
# ======================================================================

def _resolve_provider_db_ids(db, provider_name: str, model: str):
    """Resolve provider_id and model_id from the database."""
    provider_config = PROVIDER_CONFIG.get(
        provider_name, {"display_name": provider_name.title(), "base_url": None}
    )
    provider_id = db.get_or_create_provider(
        name=provider_config["display_name"],
        base_url=provider_config["base_url"],
        logo_url=None,
    )
    model_id = None
    if provider_id:
        model_id = db.get_or_create_model(
            model_name=model,
            provider_id=provider_id,
            context_window=None,
        )
    return provider_id, model_id


def _try_save_benchmark(db, run_id: str, provider_id, model_id,
                        provider_name: str, model: str,
                        result: Dict[str, Any]) -> bool:
    """Prepare benchmark data and save to DB.  Returns True on success."""
    benchmark_data = {
        "run_id": run_id,
        "provider_id": provider_id,
        "model_id": model_id,
        "provider": provider_name,
        "model": model,
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "total_latency_ms": result.get("total_latency_ms") or result.get("latency_ms", 0),
        "ttft_ms": result.get("ttft_ms"),
        "tps": result.get("tps"),
        "status_code": result.get("status_code"),
        "cost_usd": result["cost_usd"],
        "success": result["success"],
        "error_message": result.get("error_message"),
        "response_text": result.get("response_text"),
    }

    filtered = {}
    for k, v in benchmark_data.items():
        if k in ("provider_id", "model_id"):
            filtered[k] = v
        elif v is not None:
            filtered[k] = v

    return db.save_benchmark(**filtered)


def _print_success(provider_name: str, result: Dict[str, Any]):
    latency = result.get("total_latency_ms") or result.get("latency_ms", 0)
    ttft = result.get("ttft_ms")
    tps = result.get("tps")
    print(f"  ✅ {provider_name}: {latency:.0f}ms"
          f"{f'  TTFT {ttft:.0f}ms' if ttft else ''}"
          f"{f'  {tps:.1f} tps' if tps else ''}"
          f"  ${result['cost_usd']:.6f}")


# ======================================================================
# Per-provider coroutine
# ======================================================================

async def _run_single_provider(
    sem: asyncio.Semaphore,
    provider_name: str,
    func: Callable,
    model: str,
    db,
    run_id: str,
) -> Dict[str, Any]:
    """
    Run one provider benchmark inside a semaphore gate.

    Returns a dict with keys:
        provider_name, model, result, provider_id, model_id, status
    where status is one of: "success", "failed", "rate_limited", "crash".
    """
    async with sem:
        provider_id = None
        model_id = None

        try:
            # DB lookups are sync and fast
            provider_id, model_id = _resolve_provider_db_ids(db, provider_name, model)

            # The actual async API call
            result = await func(BENCHMARK_PROMPT, model)

        except Exception as e:
            return {
                "provider_name": provider_name,
                "model": model,
                "result": None,
                "provider_id": provider_id,
                "model_id": model_id,
                "status": "crash",
                "error": str(e),
            }

        # Classify the outcome
        if not result.get("success", False):
            error_type = result.get("error_type", "UNKNOWN_ERROR")
            if error_type == "RATE_LIMIT" or result.get("status_code") == 429:
                status = "rate_limited"
            else:
                status = "failed"
        else:
            status = "success"

        return {
            "provider_name": provider_name,
            "model": model,
            "result": result,
            "provider_id": provider_id,
            "model_id": model_id,
            "status": status,
            "error": result.get("error_message") if status == "failed" else None,
        }


# ======================================================================
# Main async entry point
# ======================================================================

async def async_run_benchmark(
    run_name: str,
    triggered_by: str,
    provider_filter: Optional[List[str]] = None,
    max_concurrent: int = MAX_CONCURRENT,
):
    """
    Async benchmark runner — executes all providers concurrently.

    Args:
        run_name:        Name of the run.
        triggered_by:    Who triggered the run.
        provider_filter: Optional list of provider keys to test.
        max_concurrent:  Max simultaneous API calls (semaphore size).
    """
    print(f"🚀 Starting ASYNC benchmark run: {run_name}")
    print(f"   Triggered by: {triggered_by}")
    print(f"   Max concurrency: {max_concurrent}")
    if provider_filter:
        print(f"   Provider filter: {', '.join(provider_filter)}\n")
    else:
        print("   Testing all providers\n")

    db = get_db_client()

    # ------------------------------------------------------------------
    # Budget check
    # ------------------------------------------------------------------
    print("=" * 60)
    print("BUDGET CHECK")
    print("=" * 60)
    try:
        breaker = BudgetCircuitBreaker()
        budget_status = breaker.check_budget(db, hours=24)
        print(breaker.get_status_message(db, hours=24))
        if budget_status["should_abort"]:
            print("\n🚨 ABORTING: Budget exceeded!")
            return
    except Exception as e:
        print(f"⚠️  Budget check failed: {e} — continuing (fail-open)")
    print("=" * 60 + "\n")

    # ------------------------------------------------------------------
    # Create run
    # ------------------------------------------------------------------
    run_manager = RunManager(run_name, triggered_by)
    run_manager.start()
    if not run_manager.run_id:
        print("ERROR: Could not create run")
        return

    # ------------------------------------------------------------------
    # Gather providers
    # ------------------------------------------------------------------
    all_providers = get_async_providers()

    if provider_filter:
        all_providers = [
            (prov, func, model)
            for prov, func, model in all_providers
            if prov in provider_filter
        ]
        print(f"Filtered to {len(all_providers)} provider(s)")

    total_providers = len(all_providers)
    successful = 0
    failed = 0
    rate_limited_queued = 0

    # ------------------------------------------------------------------
    # PASS 1 — Run all providers concurrently
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"⚡ PASS 1 — Running {total_providers} providers concurrently "
          f"(max {max_concurrent} at a time)")
    print(f"{'=' * 60}\n")

    sem = asyncio.Semaphore(max_concurrent)

    tasks = [
        _run_single_provider(sem, prov, func, model, db, run_manager.run_id)
        for prov, func, model in all_providers
    ]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    # Process outcomes
    pending_retries: List[Dict[str, Any]] = []

    for outcome in outcomes:
        # asyncio.gather with return_exceptions=True can return exceptions
        if isinstance(outcome, Exception):
            print(f"  ❌ Unexpected gather exception: {outcome}")
            failed += 1
            continue

        pname = outcome["provider_name"]
        pmodel = outcome["model"]
        status = outcome["status"]

        if status == "crash":
            print(f"  💥 {pname}/{pmodel}: CRASH — {outcome['error']}")
            db.save_run_error(
                run_id=run_manager.run_id,
                provider=pname,
                model=pmodel,
                error_type="PROVIDER_CRASH",
                error_message=f"Provider crashed: {outcome['error']}",
                status_code=None,
                provider_id=outcome["provider_id"],
                model_id=outcome["model_id"],
            )
            failed += 1

        elif status == "rate_limited":
            print(f"  ⏳ {pname}/{pmodel}: rate-limited — deferred for retry")
            pending_retries.append(outcome)

        elif status == "failed":
            result = outcome["result"]
            print(f"  ❌ {pname}/{pmodel}: {result.get('error_message', 'Unknown')}")
            db.save_run_error(
                run_id=run_manager.run_id,
                provider=pname,
                model=pmodel,
                error_type=result.get("error_type", "UNKNOWN_ERROR"),
                error_message=result.get("error_message", "Unknown error"),
                status_code=result.get("status_code"),
                provider_id=outcome["provider_id"],
                model_id=outcome["model_id"],
            )
            failed += 1

        else:  # success
            result = outcome["result"]
            save_ok = _try_save_benchmark(
                db, run_manager.run_id,
                outcome["provider_id"], outcome["model_id"],
                pname, pmodel, result,
            )
            _print_success(pname, result)
            if save_ok:
                successful += 1
            else:
                print(f"  ⚠️  {pname}/{pmodel}: DB save failed")
                failed += 1

    # ------------------------------------------------------------------
    # DEFERRED RETRY ROUNDS — rate-limited providers (sequential)
    # ------------------------------------------------------------------
    if pending_retries:
        print(f"\n{'=' * 60}")
        print(f"⏳ {len(pending_retries)} provider(s) rate-limited — starting deferred retries")
        print(f"   Strategy: {DEFERRED_RETRY_ROUNDS} rounds, {DEFERRED_COOLDOWN_SECS}s cooldown")
        print(f"{'=' * 60}")

    for retry_round in range(1, DEFERRED_RETRY_ROUNDS + 1):
        if not pending_retries:
            break

        print(f"\n{'─' * 60}")
        print(f"⏱  Round {retry_round}/{DEFERRED_RETRY_ROUNDS} "
              f"— cooldown {DEFERRED_COOLDOWN_SECS}s ...")
        print(f"{'─' * 60}")
        await asyncio.sleep(DEFERRED_COOLDOWN_SECS)

        # Retry all pending concurrently within the semaphore
        retry_tasks = []
        for item in pending_retries:
            # Re-lookup the async function from the cached provider service
            # (already loaded during pass 1)
            prov_key = item["provider_name"]
            pmodel = item["model"]
            # We need the function again — find it in original list
            func = None
            for p, f, m in all_providers:
                if p == prov_key and m == pmodel:
                    func = f
                    break
            if func is None:
                continue
            retry_tasks.append(
                _run_single_provider(sem, prov_key, func, pmodel, db, run_manager.run_id)
            )

        retry_outcomes = await asyncio.gather(*retry_tasks, return_exceptions=True)

        still_pending: List[Dict[str, Any]] = []

        for outcome in retry_outcomes:
            if isinstance(outcome, Exception):
                failed += 1
                continue

            pname = outcome["provider_name"]
            pmodel = outcome["model"]
            status = outcome["status"]

            if status == "rate_limited":
                print(f"  ⏳ {pname}/{pmodel}: still rate-limited")
                still_pending.append(outcome)
            elif status in ("crash", "failed"):
                err = outcome.get("error") or (outcome.get("result", {}) or {}).get("error_message", "Unknown")
                print(f"  ❌ {pname}/{pmodel}: {err}")
                db.save_run_error(
                    run_id=run_manager.run_id,
                    provider=pname, model=pmodel,
                    error_type=outcome.get("result", {}).get("error_type", "UNKNOWN_ERROR") if outcome.get("result") else "PROVIDER_CRASH",
                    error_message=str(err),
                    status_code=(outcome.get("result") or {}).get("status_code"),
                    provider_id=outcome["provider_id"],
                    model_id=outcome["model_id"],
                )
                failed += 1
            else:
                result = outcome["result"]
                save_ok = _try_save_benchmark(
                    db, run_manager.run_id,
                    outcome["provider_id"], outcome["model_id"],
                    pname, pmodel, result,
                )
                _print_success(pname, result)
                if save_ok:
                    successful += 1
                    print(f"  ✅ {pname}/{pmodel}: deferred retry succeeded")
                else:
                    failed += 1

        pending_retries = still_pending

    # ------------------------------------------------------------------
    # Push remaining to DB queue
    # ------------------------------------------------------------------
    if pending_retries:
        print(f"\n⚠️  {len(pending_retries)} provider(s) still rate-limited "
              f"— pushing to DB queue")
        for item in pending_retries:
            pname = item["provider_name"]
            pmodel = item["model"]
            try:
                success = db.enqueue_benchmarks(
                    run_id=run_manager.run_id,
                    provider_models=[(pname, pmodel)],
                )
                if success:
                    print(f"  📥 {pname}/{pmodel} → queued")
                    rate_limited_queued += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ⚠️  Queue error {pname}/{pmodel}: {e}")
                failed += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("Benchmark COMPLETE! (async)")
    print(f"{'=' * 60}")
    print(f"\n📊 Summary:")
    print(f"   Total Providers: {total_providers}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    if rate_limited_queued:
        print(f"   ⏳ Rate Limited (queued): {rate_limited_queued}")
        print(f"\n💡 Tip: Run queue_benchmark_runner.py to retry queued providers")

    if failed == 0 and rate_limited_queued == 0:
        status_msg = "All providers succeeded"
    elif failed == 0:
        status_msg = f"Success (with {rate_limited_queued} queued for retry)"
    elif successful == 0:
        status_msg = "All providers failed"
    else:
        status_msg = f"Completed with {failed} error(s)"
        if rate_limited_queued:
            status_msg += f" and {rate_limited_queued} queued"

    print(f"   Status: {status_msg}")
    print(f"{'=' * 60}")

    run_manager.end()


# ======================================================================
# Convenience: run from sync context
# ======================================================================

def run_async_benchmark(
    run_name: str = "async-benchmark",
    triggered_by: str = "system",
    provider_filter: Optional[List[str]] = None,
    max_concurrent: int = MAX_CONCURRENT,
):
    """Sync wrapper — creates event loop and runs the async benchmark."""
    asyncio.run(
        async_run_benchmark(run_name, triggered_by, provider_filter, max_concurrent)
    )
