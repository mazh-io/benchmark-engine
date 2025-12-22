from benchmarking.run_manager import RunManager
from database.supabase_client import save_benchmark, get_or_create_provider, get_or_create_model, save_price

from utils.constants import BENCHMARK_PROMPT, PROVIDER_CONFIG, PROVIDERS

def run_benchmark(run_name: str, triggered_by: str):
    """
    Main function that executes the benchmark for all providers.
    
    Args:
        run_name: Name of the run (e.g. "mvp-validation-run")
        triggered_by: Who triggered the run (e.g. "system")
    
    Process:
        1. Create a new run in db
        2. Test each provider sequentially without concurrency
        3. Save results to db
        4. End the run
    """
    print(f"Starting benchmark run: {run_name}")
    print(f"Triggered by: {triggered_by}\n")

    # Create Runmanager to manage the lifecycle of the run
    run_manager = RunManager(run_name, triggered_by)
    run_manager.start()  # Create run in db and get its UUID

    # Check if the run was created successfully
    if not run_manager.run_id:
        print("ERROR: Could not create run")
        return

    # Test each provider sequentially without concurrency
    for provider_name, func, model in PROVIDERS:
        print("\n" + "=" * 60)
        print(f"Testing → {provider_name} / {model}")
        print("=" * 60)
        
        # Get or create provider in database
        provider_config = PROVIDER_CONFIG.get(provider_name, {"display_name": provider_name.title(), "base_url": None})
        provider_id = get_or_create_provider(
            name=provider_config["display_name"],
            base_url=provider_config["base_url"],
            logo_url=None
        )
        
        # Get or create model in database (requires provider_id)
        model_id = None
        if provider_id:
            model_id = get_or_create_model(
                name=model,
                provider_id=provider_id,
                context_window=None  # Can be added later if needed
            )
        
        # Call the provider function with the prompt and model to get a dictionary with the results
        # This will return a dictionary with the results
        result = func(BENCHMARK_PROMPT, model)

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
        
        save_result = save_benchmark(**benchmark_data)

        # Print results to console
        if result["success"]:
            print(f" Success ({provider_name})")
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
        else:
            print(f"Failed: {result['error_message']}")

        # Confirm if results were saved to db
        if save_result:
            print(" Saved to DB")
        else:
            print(" DB Error")

    # End the run
    print("\n" + "=" * 60)
    print("Benchmark DONE!")
    print("=" * 60)

    run_manager.end()
