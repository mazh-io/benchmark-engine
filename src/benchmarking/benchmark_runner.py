from benchmarking.run_manager import RunManager
from database.supabase_client import save_benchmark, get_or_create_provider, get_or_create_model

from providers.openai_provider import call_openai
from providers.groq_provider import call_groq
from providers.together_provider import call_together
from providers.openrouter_provider import call_openrouter



# Prompt that we are using for benchmarking
# AI should summarize this text into exactly three concise bullet points
BENCHMARK_PROMPT = """The history of timekeeping is a testament to humanity's obsession with measuring the passage of existence. Before the mechanical precision of modern clocks, early civilizations relied on the celestial bodies to organize their lives. The sun, moon, and stars provided the first canvas for tracking time. The Egyptians, for instance, constructed towering obelisks that cast shadows, effectively functioning as primitive sundials that divided the day into segments. However, these devices had a significant limitation: they were useless at night or on cloudy days.

To overcome the reliance on the sun, the Greeks and Romans refined the water clock, or clepsydra. These devices measured time by the regulated flow of water into or out of a vessel. While more consistent than sundials, they required constant maintenance to ensure the flow remained steady despite temperature changes affecting the water's viscosity. Simultaneously, in the East, incense clocks burned at a known rate, providing a scented measure of passing hours in temples and homes.

The true revolution occurred in medieval Europe with the invention of the mechanical escapement mechanism. This innovation allowed for the controlled release of energy from a falling weight, translating it into the rhythmic ticking sound we associate with clocks today. These early mechanical clocks, often installed in town towers, did not have faces or hands; they simply rang bells to signal the hour for prayer and work. They were the heartbeat of the medieval city, synchronizing the community's labor and worship.

By the 17th century, the pendulum clock, introduced by Christiaan Huygens, brought unprecedented accuracy, reducing the deviation from minutes per day to seconds. This leap forward enabled scientists to conduct more precise experiments and navigators to begin solving the problem of longitude at sea. The evolution continued with the shrinking of mechanisms into pocket watches and eventually wristwatches, democratizing time and strapping it to the individual's arm.

Today, we rely on atomic clocks, which measure time based on the vibration of cesium atoms. These devices are so accurate that they would lose less than a second in millions of years. This hyper-precision underpins the GPS technology that guides our cars and the internet protocols that synchronize our global communication networks. From the shadow of an obelisk to the vibration of an atom, the history of timekeeping is a journey from observing nature to mastering the fundamental forces of physics."""


# Provider configuration mapping
# Maps internal provider name to display name and base URL
PROVIDER_CONFIG = {
    "openai": {
        "display_name": "OpenAI",
        "base_url": "https://api.openai.com"
    },
    "groq": {
        "display_name": "Groq",
        "base_url": "https://api.groq.com"
    },
    "together": {
        "display_name": "Together AI",
        "base_url": "https://api.together.xyz"
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "base_url": "https://openrouter.ai"
    }
}

# List of providers that we are testing
# Format: provider_name function model_name
PROVIDERS = [
    ("openai", call_openai, "gpt-4o-mini"),
    ("groq", call_groq, "llama-3.1-8b-instant"),
    ("together", call_together, "mistralai/Mixtral-8x7B-Instruct-v0.1"),
    ("openrouter", call_openrouter, "openai/gpt-4o-mini"),
]


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
