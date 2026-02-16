from benchmarking.run_manager import RunManager
from database.db_connector import get_db_client

from utils.constants import BENCHMARK_PROMPT, PROVIDER_CONFIG
from utils.provider_service import get_providers
from utils.budget_breaker import BudgetCircuitBreaker, BudgetExceededException
from typing import Optional, List

def run_benchmark(run_name: str, triggered_by: str, provider_filter: Optional[List[str]] = None):
    """
    Main function that executes the benchmark for all providers.
    
    Args:
        run_name: Name of the run (e.g. "mvp-validation-run")
        triggered_by: Who triggered the run (e.g. "system")
        provider_filter: Optional list of provider keys to test (e.g., ["openai", "groq"])
                        If None, tests all providers
    
    Process:
        1. Check budget (abort if exceeded)
        2. Create a new run in db
        3. Test each provider sequentially without concurrency
        4. Save results to db
        5. End the run
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
    print("\n" + "="*60)
    print("BUDGET CHECK")
    print("="*60)
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
    
    print("="*60 + "\n")

    # Create Runmanager to manage the lifecycle of the run
    run_manager = RunManager(run_name, triggered_by)
    run_manager.start()  # Create run in db and get its UUID

    # Check if the run was created successfully
    if not run_manager.run_id:
        print("ERROR: Could not create run")
        return

    # Test each provider sequentially without concurrency
    # Track success/failure for final summary
    all_providers = get_providers()
    
    # Filter providers if filter is provided
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
    
    for provider_name, func, model in all_providers:
        print("\n" + "=" * 60)
        print(f"Testing → {provider_name} / {model}")
        print("=" * 60)
        
        try:
            # Get or create provider in database
            provider_config = PROVIDER_CONFIG.get(provider_name, {"display_name": provider_name.title(), "base_url": None})
            provider_id = db.get_or_create_provider(
                name=provider_config["display_name"],
                base_url=provider_config["base_url"],
                logo_url=None
            )
            
            # Get or create model in database (requires provider_id)
            # Model name is automatically normalized by get_or_create_model()
            # e.g., "accounts/fireworks/models/llama-v3p3-70b" → "llama-3.3-70b"
            model_id = None
            if provider_id:
                model_id = db.get_or_create_model(
                    model_name=model,
                    provider_id=provider_id,
                    context_window=None  # Can be added later if needed
                )
            
            # Call the provider function with the prompt and model to get a dictionary with the results
            # This is wrapped in a try-catch to ensure one failing provider doesn't crash the whole run
            result = func(BENCHMARK_PROMPT, model)
        
        except Exception as e:
            # CRITICAL: If provider function crashes completely, log error and continue
            error_message = f"Provider function crashed: {str(e)}"
            print(f"CRITICAL ERROR ({provider_name}): {error_message}")
            
            # Save error to database
            db.save_run_error(
                run_id=run_manager.run_id,
                provider=provider_name,
                model=model,
                error_type="PROVIDER_CRASH",
                error_message=error_message,
                status_code=None,
                provider_id=provider_id if 'provider_id' in locals() else None,
                model_id=model_id if 'model_id' in locals() else None
            )
            
            failed_providers += 1
            print(f" Continuing with next provider...")
            continue  # IMPORTANT: Continue to next provider
        
        # Check if the call was successful or returned an error
        if not result.get("success", False):
            # Provider returned an error result (but didn't crash)
            error_type = result.get("error_type", "UNKNOWN_ERROR")
            
            # If rate limited, add to benchmark_queue for retry later
            if error_type == "RATE_LIMIT" and result.get("status_code") == 429:
                print(f"⏳ Rate limited - checking queue status")
                
                # Check if already queued for this run to avoid duplicates
                try:
                    queue_stats = db.get_queue_stats(run_manager.run_id)
                    
                    # Check if this provider/model combo is already in queue
                    # We'll query the queue directly to check for existing items
                    existing_queue = False
                    if hasattr(db, 'supabase'):
                        response = db.supabase.table("benchmark_queue").select("id, attempts, max_attempts, status").eq(
                            "run_id", run_manager.run_id
                        ).eq("provider_key", provider_name).eq("model_name", model).execute()
                        
                        if response.data:
                            item = response.data[0]
                            if item['status'] in ['pending', 'processing']:
                                existing_queue = True
                                print(f"⚠️  Already queued (attempts: {item['attempts']}/{item['max_attempts']})")
                            elif item['status'] == 'failed' and item['attempts'] >= item['max_attempts']:
                                print(f"❌ Max retry attempts reached ({item['attempts']}/{item['max_attempts']}) - not queueing")
                                failed_providers += 1
                                continue
                    else:
                        # Local PostgreSQL check
                        conn = db._get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT id, attempts, max_attempts, status 
                            FROM benchmark_queue 
                            WHERE run_id = %s AND provider_key = %s AND model_name = %s
                            LIMIT 1
                        """, (run_manager.run_id, provider_name, model))
                        result_row = cur.fetchone()
                        cur.close()
                        conn.close()
                        
                        if result_row:
                            item_id, attempts, max_attempts, status = result_row
                            if status in ['pending', 'processing']:
                                existing_queue = True
                                print(f"⚠️  Already queued (attempts: {attempts}/{max_attempts})")
                            elif status == 'failed' and attempts >= max_attempts:
                                print(f"❌ Max retry attempts reached ({attempts}/{max_attempts}) - not queueing")
                                failed_providers += 1
                                continue
                    
                    if not existing_queue:
                        # Add to queue with max_attempts = 3
                        success = db.enqueue_benchmarks(
                            run_id=run_manager.run_id,
                            provider_models=[(provider_name, model)]
                        )
                        
                        if success:
                            print(f"✅ Added to queue - will retry up to 3 times via queue_benchmark_runner")
                            rate_limited_count += 1
                        else:
                            print(f"⚠️  Failed to add to queue")
                            failed_providers += 1
                    
                except Exception as e:
                    print(f"⚠️  Queue check failed: {e}")
                    failed_providers += 1
                
                print(f"✓ Continuing with next provider...")
                continue
            
            # For other errors, log and continue
            print(f"❌ Failed: {result.get('error_message', 'Unknown error')}")
            
            # Save error to database
            db.save_run_error(
                run_id=run_manager.run_id,
                provider=provider_name,
                model=model,
                error_type=error_type,
                error_message=result.get("error_message", "Unknown error"),
                status_code=result.get("status_code"),
                provider_id=provider_id,
                model_id=model_id
            )
            
            failed_providers += 1
            print(f"✓ Continuing with next provider...")
            continue  # Continue to next provider

        # Save results to db
        # Prepare data for saving (only include fields that exist in schema)
        benchmark_data = {
            "run_id": run_manager.run_id,
            "provider_id": provider_id,  # Foreign key to providers table
            "model_id": model_id,  # Foreign key to models table
            "provider": provider_name,  # Legacy field for backward compatibility
            "model": model,  # Legacy field for backward compatibility
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "total_latency_ms": result.get("total_latency_ms") or result.get("latency_ms", 0),
            "ttft_ms": result.get("ttft_ms"),
            "tps": result.get("tps"),
            "status_code": result.get("status_code"),
            "cost_usd": result["cost_usd"],
            "success": result["success"],
            "error_message": result.get("error_message"),
            "response_text": result.get("response_text")
        }
        
        # Remove None values to avoid issues (but keep provider_id and model_id even if None - they're nullable in schema)
        # Only remove None for non-nullable fields
        filtered_data = {}
        for k, v in benchmark_data.items():
            # Keep provider_id and model_id even if None (they're nullable foreign keys)
            if k in ["provider_id", "model_id"]:
                filtered_data[k] = v
            elif v is not None:
                filtered_data[k] = v
        
        benchmark_data = filtered_data
        
        save_result = db.save_benchmark(**benchmark_data)

        # Print results to console
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

        # Confirm if results were saved to db
        if save_result:
            print("✅ Saved to DB")
            successful_providers += 1
        else:
            print("⚠️  DB Error")
            failed_providers += 1

    # End the run
    print("\n" + "=" * 60)
    print("Benchmark COMPLETE!")
    print("=" * 60)
    
    # Print summary
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
