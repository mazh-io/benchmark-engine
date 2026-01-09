# Global constants for the benchmark engine

BENCHMARK_PROMPT = """The history of timekeeping is a testament to humanity's obsession with measuring the passage of existence. Before the mechanical precision of modern clocks, early civilizations relied on the celestial bodies to organize their lives. The sun, moon, and stars provided the first canvas for tracking time. The Egyptians, for instance, constructed towering obelisks that cast shadows, effectively functioning as primitive sundials that divided the day into segments. However, these devices had a significant limitation: they were useless at night or on cloudy days.

To overcome the reliance on the sun, the Greeks and Romans refined the water clock, or clepsydra. These devices measured time by the regulated flow of water into or out of a vessel. While more consistent than sundials, they required constant maintenance to ensure the flow remained steady despite temperature changes affecting the water's viscosity. Simultaneously, in the East, incense clocks burned at a known rate, providing a scented measure of passing hours in temples and homes.

The true revolution occurred in medieval Europe with the invention of the mechanical escapement mechanism. This innovation allowed for the controlled release of energy from a falling weight, translating it into the rhythmic ticking sound we associate with clocks today. These early mechanical clocks, often installed in town towers, did not have faces or hands; they simply rang bells to signal the hour for prayer and work. They were the heartbeat of the medieval city, synchronizing the community's labor and worship.

By the 17th century, the pendulum clock, introduced by Christiaan Huygens, brought unprecedented accuracy, reducing the deviation from minutes per day to seconds. This leap forward enabled scientists to conduct more precise experiments and navigators to begin solving the problem of longitude at sea. The evolution continued with the shrinking of mechanisms into pocket watches and eventually wristwatches, democratizing time and strapping it to the individual's arm.

Today, we rely on atomic clocks, which measure time based on the vibration of cesium atoms. These devices are so accurate that they would lose less than a second in millions of years. This hyper-precision underpins the GPS technology that guides our cars and the internet protocols that synchronize our global communication networks. From the shadow of an obelisk to the vibration of an atom, the history of timekeeping is a journey from observing nature to mastering the fundamental forces of physics."""

# System prompt used across all providers for consistent benchmarking
SYSTEM_PROMPT = (
    "You are a helpful assistant. Your task is to summarize the provided "
    "text into exactly three concise bullet points."
)

# Maximum tokens to generate (used by providers that require this parameter)
MAX_TOKENS = 1024

# Provider configuration - defined before importing provider functions to avoid circular imports
PROVIDER_CONFIG = {
    # Existing providers
    "openai": {
        "display_name": "OpenAI",
        "base_url": "https://api.openai.com",
        "pricing_url": "https://openai.com/api/pricing/",
        "default_pricing": {"input": 0.15, "output": 0.60},  # GPT-4o-mini rates
    },
    "groq": {
        "display_name": "Groq",
        "base_url": "https://api.groq.com",
        "pricing_url": "https://groq.com/pricing",
        "default_pricing": {"input": 0.20, "output": 0.20},
    },
    "together": {
        "display_name": "Together AI",
        "base_url": "https://api.together.xyz",
        "models_url": "https://api.together.xyz/v1/models",
        "default_pricing": {"input": 0.60, "output": 0.60},
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "base_url": "https://openrouter.ai",
        "pricing_url": "https://openrouter.ai/api/v1/models",
        "default_pricing": {"input": 0.20, "output": 0.60},  # Average across models
    },
    # New providers (Phase 2)
    "deepseek": {
        "display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "pricing_url": "https://api-docs.deepseek.com/quick_start/pricing",
        "default_pricing": {"input": 0.28, "output": 0.42},  # DeepSeek-V3.2 cache miss rates
    },
    "cerebras": {
        "display_name": "Cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "pricing_url": "https://www.cerebras.ai/",
        "default_pricing": {"input": 0.60, "output": 0.60},
    },
    "mistral": {
        "display_name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "pricing_url": "https://mistral.ai/technology/#pricing",
        "default_pricing": {"input": 2.00, "output": 6.00},
    },
    "fireworks": {
        "display_name": "Fireworks AI",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "pricing_url": "https://fireworks.ai/pricing",
        "default_pricing": {"input": 0.90, "output": 0.90},
    },
    "sambanova": {
        "display_name": "SambaNova",
        "base_url": "https://api.sambanova.ai/v1",
        "pricing_url": "https://cloud.sambanova.ai/pricing",
        "default_pricing": {"input": 0.60, "output": 1.20},  # Meta-Llama rates
    },
    # Phase 3 - Custom SDK Providers
    "anthropic": {
        "display_name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "pricing_url": "https://www.anthropic.com/pricing",
        "default_pricing": {"input": 3.00, "output": 15.00},
    },
    "google": {
        "display_name": "Google",
        "base_url": "https://generativelanguage.googleapis.com",
        "pricing_url": "https://ai.google.dev/pricing",
        "default_pricing": {"input": 1.25, "output": 5.00},
    },
}