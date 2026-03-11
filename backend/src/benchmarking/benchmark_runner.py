import time

from benchmarking.run_manager import RunManager
from database.db_connector import get_db_client

from utils.constants import BENCHMARK_PROMPT, PROVIDER_CONFIG
from utils.provider_service import get_providers
from utils.budget_breaker import BudgetCircuitBreaker, BudgetExceededException
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Configuration for deferred retry behaviour
# ---------------------------------------------------------------------------
DEFERRED_RETRY_ROUNDS = 3       # How many retry rounds after the main pass
DEFERRED_COOLDOWN_SECS = 60     # Minimum seconds to wait before each retry round


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

    # Remove None values (keep nullable FK fields)
    filtered = {}
    for k, v in benchmark_data.items():
        if k in ("provider_id", "model_id"):
            filtered[k] = v
        elif v is not None:
            filtered[k] = v

    return db.save_benchmark(**filtered)


def _print_success(provider_name: str, result: Dict[str, Any]):
    """Pretty-print a successful benchmark result."""
    print(f"Success ({provider_name})")
    latency = result.get("total_latency_ms") or result.get("latency_ms", 0)
    print(f"   Total Latency: {latency:.2f} ms")
    if result.get("ttft_ms"):
        print(f"   TTFT: {result['ttft_ms']:.2f} ms")
    if result.get("tps"):
        print(f"   TPS: {result['tps']:.2f} tokens/sec")
    print(f"   Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
    print(f"   Cost: ${result['cost_usd']:.6f}")
    if result.get("status_code"):
        print(f"   Status: {result['status_code']}")


def run_benchmark(run_name: str, triggered_by: str, provider_filter: Optional[List[str]] = None):
    """
    Main function that executes the benchmark for all providers.

    Uses a **deferred retry** strategy for rate-limited (429) providers:
      1. Pass 1 — try every provider sequentially.
         • 5xx errors are retried inline (1s→2s→4s via retry_with_backoff).
         • 429 rate limits are collected in an in-memory *pending* list.
      2. Cooldown — wait DEFERRED_COOLDOWN_SECS so rate limits can reset.
      3. Pass 2..N — retry pending providers (up to DEFERRED_RETRY_ROUNDS).
      4. Any still-failing providers are pushed to the DB queue for
         queue_benchmark_runner.py to handle later.

    This avoids blocking the whole run while a single provider is rate-limited.
    
    Architecture note — why not Celery?
      Celery + Redis would enable *concurrent* benchmarking (all providers in
      parallel) with automatic retry scheduling.  That's the right next step
      if sequential runs become too slow.  For now the deferred-retry approach
      gives 90% of the benefit with zero infrastructure overhead.

    Args:
        run_name: Name of the run (e.g. "mvp-validation-run")
        triggered_by: Who triggered the run (e.g. "system")
        provider_filter: Optional list of provider keys to test
    """
    print(f"Starting benchmark run: {run_name}")
    print(f"Triggered by: {triggered_by}")
    if provider_filter:
        print(f"Provider filter: {', '.join(provider_filter)}\n")
    else:
        print("Testing all providers\n")

    # Get database client
    db = get_db_client()

    # 🚨 BUDGET CHECK: Prevent runaway costs
    print("\n" + "=" * 60)
    print("BUDGET CHECK")
    print("=" * 60)
    try:
        breaker = BudgetCircuitBreaker()
        budget_status = breaker.check_budget(db, hours=24)
        print(breaker.get_status_message(db, hours=24))

        if budget_status["should_abort"]:
            print("\n🚨 ABORTING: Budget exceeded!")
            print("To increase budget, set BENCHMARK_BUDGET_CAP environment variable.")
            print("Example: export BENCHMARK_BUDGET_CAP=25.0")
            return
    except Exception as e:
        print(f"⚠️  Budget check failed: {e}")
        print("Continuing with benchmark (fail-open safety)...")

    print("=" * 60 + "\n")

    # Create RunManager to manage the lifecycle of the run
    run_manager = RunManager(run_name, triggered_by)
    run_manager.start()

    if not run_manager.run_id:
        print("ERROR: Could not create run")
        return

    # ------------------------------------------------------------------
    # Gather provider list
    # ------------------------------------------------------------------
    all_providers = get_providers()

    if provider_filter:
        all_providers = [
            (prov, func, model)
            for prov, func, model in all_providers
            if prov in provider_filter
        ]
        print(f"Filtered to {len(all_providers)} provider(s)")

    total_providers = len(all_providers)
    successful_providers = 0
    failed_providers = 0
    rate_limited_count = 0

    # In-memory pending list for rate-limited providers
    # Each entry: {"provider_name": str, "func": callable, "model": str,
    #              "provider_id": str|None, "model_id": str|None}
    pending_retries: List[Dict[str, Any]] = []

    # ==================================================================
    # PASS 1 — Try every provider
    # ==================================================================
    last_provider: Optional[str] = None
    for provider_name, func, model in all_providers:
        # Per-provider delay: throttle calls to rate-limited providers
        if provider_name == last_provider:
            delay_s = PROVIDER_CONFIG.get(provider_name, {}).get("inter_call_delay_s", 0)
            if delay_s > 0:
                print(f"⏳ {provider_name}: waiting {delay_s}s (rate limit throttle)")
                time.sleep(delay_s)
        last_provider = provider_name

        print("\n" + "=" * 60)
        print(f"Testing → {provider_name} / {model}")
        print("=" * 60)

        provider_id = None
        model_id = None

        try:
            provider_id, model_id = _resolve_provider_db_ids(db, provider_name, model)
            result = func(BENCHMARK_PROMPT, model)

        except Exception as e:
            error_message = f"Provider function crashed: {str(e)}"
            print(f"CRITICAL ERROR ({provider_name}): {error_message}")
            db.save_run_error(
                run_id=run_manager.run_id,
                provider=provider_name,
                model=model,
                error_type="PROVIDER_CRASH",
                error_message=error_message,
                status_code=None,
                provider_id=provider_id,
                model_id=model_id,
            )
            failed_providers += 1
            print(f"  Continuing with next provider...")
            continue

        # ---- Handle error results (provider didn't crash) ----
        if not result.get("success", False):
            error_type = result.get("error_type", "UNKNOWN_ERROR")

            if error_type == "RATE_LIMIT" and result.get("status_code") == 429:
                # Don't block — defer to retry after all other providers finish
                print(f"⏳ Rate limited — deferring to retry after other providers")
                pending_retries.append({
                    "provider_name": provider_name,
                    "func": func,
                    "model": model,
                    "provider_id": provider_id,
                    "model_id": model_id,
                })
                continue

            # Non-rate-limit errors: log and continue
            print(f"❌ Failed: {result.get('error_message', 'Unknown error')}")
            db.save_run_error(
                run_id=run_manager.run_id,
                provider=provider_name,
                model=model,
                error_type=error_type,
                error_message=result.get("error_message", "Unknown error"),
                status_code=result.get("status_code"),
                provider_id=provider_id,
                model_id=model_id,
            )
            failed_providers += 1
            print(f"✓ Continuing with next provider...")
            continue

        # ---- Success ----
        save_ok = _try_save_benchmark(
            db, run_manager.run_id, provider_id, model_id,
            provider_name, model, result,
        )
        _print_success(provider_name, result)

        if save_ok:
            print("✅ Saved to DB")
            successful_providers += 1
        else:
            print("⚠️  DB Error")
            failed_providers += 1

    # ==================================================================
    # DEFERRED RETRY ROUNDS — retry rate-limited providers
    # ==================================================================
    if pending_retries:
        print("\n" + "=" * 60)
        print(f"⏳ {len(pending_retries)} provider(s) were rate-limited — starting deferred retries")
        print(f"   Strategy: up to {DEFERRED_RETRY_ROUNDS} rounds, {DEFERRED_COOLDOWN_SECS}s cooldown between rounds")
        print("=" * 60)

    for retry_round in range(1, DEFERRED_RETRY_ROUNDS + 1):
        if not pending_retries:
            break

        # Use the largest inter_call_delay_s among pending providers,
        # falling back to DEFERRED_COOLDOWN_SECS as a minimum.
        cooldown = max(
            DEFERRED_COOLDOWN_SECS,
            max(
                PROVIDER_CONFIG.get(item["provider_name"], {}).get("inter_call_delay_s", 0)
                for item in pending_retries
            ),
        )

        print(f"\n{'─' * 60}")
        print(f"⏱  Deferred retry round {retry_round}/{DEFERRED_RETRY_ROUNDS} "
              f"— waiting {cooldown}s cooldown...")
        print(f"{'─' * 60}")
        time.sleep(cooldown)

        still_pending: List[Dict[str, Any]] = []
        last_retry_provider: Optional[str] = None

        for item in pending_retries:
            pname = item["provider_name"]
            pfunc = item["func"]
            pmodel = item["model"]
            pid = item["provider_id"]
            mid = item["model_id"]

            # Per-provider throttle within the retry round
            if pname == last_retry_provider:
                delay_s = PROVIDER_CONFIG.get(pname, {}).get("inter_call_delay_s", 0)
                if delay_s > 0:
                    print(f"  ⏳ {pname}: waiting {delay_s}s (rate limit throttle)")
                    time.sleep(delay_s)
            last_retry_provider = pname

            print(f"\n  🔄 Retrying → {pname} / {pmodel}")

            try:
                result = pfunc(BENCHMARK_PROMPT, pmodel)
            except Exception as e:
                print(f"  ❌ Crash during retry: {e}")
                db.save_run_error(
                    run_id=run_manager.run_id,
                    provider=pname,
                    model=pmodel,
                    error_type="PROVIDER_CRASH",
                    error_message=f"Provider crashed during deferred retry: {e}",
                    status_code=None,
                    provider_id=pid,
                    model_id=mid,
                )
                failed_providers += 1
                continue

            if not result.get("success", False):
                if result.get("status_code") == 429:
                    print(f"  ⏳ Still rate-limited")
                    still_pending.append(item)
                else:
                    print(f"  ❌ Failed: {result.get('error_message', 'Unknown error')}")
                    db.save_run_error(
                        run_id=run_manager.run_id,
                        provider=pname,
                        model=pmodel,
                        error_type=result.get("error_type", "UNKNOWN_ERROR"),
                        error_message=result.get("error_message", "Unknown error"),
                        status_code=result.get("status_code"),
                        provider_id=pid,
                        model_id=mid,
                    )
                    failed_providers += 1
                continue

            # Success on retry
            save_ok = _try_save_benchmark(
                db, run_manager.run_id, pid, mid, pname, pmodel, result,
            )
            _print_success(pname, result)

            if save_ok:
                print("  ✅ Saved to DB (deferred retry succeeded)")
                successful_providers += 1
            else:
                print("  ⚠️  DB Error")
                failed_providers += 1

        pending_retries = still_pending

    # ==================================================================
    # Push remaining failures to DB queue for queue_benchmark_runner.py
    # ==================================================================
    if pending_retries:
        print(f"\n⚠️  {len(pending_retries)} provider(s) still rate-limited after "
              f"{DEFERRED_RETRY_ROUNDS} retry rounds — pushing to DB queue")

        for item in pending_retries:
            pname = item["provider_name"]
            pmodel = item["model"]
            try:
                success = db.enqueue_benchmarks(
                    run_id=run_manager.run_id,
                    provider_models=[(pname, pmodel)],
                )
                if success:
                    print(f"  📥 {pname}/{pmodel} → queued for queue_benchmark_runner")
                    rate_limited_count += 1
                else:
                    print(f"  ⚠️  Failed to enqueue {pname}/{pmodel}")
                    failed_providers += 1
            except Exception as e:
                print(f"  ⚠️  Queue error for {pname}/{pmodel}: {e}")
                failed_providers += 1

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    print("Benchmark COMPLETE!")
    print("=" * 60)

    print(f"\n📊 Summary:")
    print(f"   Total Providers: {total_providers}")
    print(f"   ✅ Successful: {successful_providers}")
    print(f"   ❌ Failed: {failed_providers}")

    if rate_limited_count > 0:
        print(f"   ⏳ Rate Limited (queued): {rate_limited_count}")
        print(f"\n💡 Tip: Run queue_benchmark_runner.py to retry rate-limited providers")

    # Determine overall status
    if failed_providers == 0:
        if rate_limited_count > 0:
            status = f"Success (with {rate_limited_count} queued for retry)"
        else:
            status = "All providers succeeded"
    elif successful_providers == 0:
        status = "All providers failed"
    else:
        status = f"Completed with {failed_providers} error(s)"
        if rate_limited_count > 0:
            status += f" and {rate_limited_count} queued"

    print(f"   Status: {status}")
    print("=" * 60)

    run_manager.end()
