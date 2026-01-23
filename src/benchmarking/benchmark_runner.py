from benchmarking.run_manager import RunManager
from database.db_connector import get_db_client

from utils.constants import BENCHMARK_PROMPT, PROVIDER_CONFIG
from utils.provider_service import get_providers
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
        1. Create a new run in db
        2. Test each provider sequentially without concurrency
        3. Save results to db
        4. End the run
    """
    print(f"Starting benchmark run: {run_name}")
    print(f"Triggered by: {triggered_by}")
    if provider_filter:
        print(f"Provider filter: {', '.join(provider_filter)}\n")
    else:
        print("Testing all providers\n")

    # Get database client
    db = get_db_client()

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
            print(f"Failed: {result.get('error_message', 'Unknown error')}")
            
            # Save error to database
            db.save_run_error(
                run_id=run_manager.run_id,
                provider=provider_name,
                model=model,
                error_type=result.get("error_type", "UNKNOWN_ERROR"),
                error_message=result.get("error_message", "Unknown error"),
                status_code=result.get("status_code"),
                provider_id=provider_id,
                model_id=model_id
            )
            
            failed_providers += 1
            print(f" Continuing with next provider...")
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
            print("Saved to DB")
            successful_providers += 1
        else:
            print(" DB Error")
            failed_providers += 1

    # End the run
    print("\n" + "=" * 60)
    print("Benchmark COMPLETE!")
    print("=" * 60)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total Providers: {total_providers}")
    print(f" Successful: {successful_providers}")
    print(f" Failed: {failed_providers}")
    
    # Determine overall status
    if failed_providers == 0:
        status = "All providers succeeded"
    elif successful_providers == 0:
        status = "All providers failed"
    else:
        status = f"Completed with {failed_providers} error(s)"
    
    print(f"   Status: {status}")
    print("=" * 60)

    run_manager.end()
