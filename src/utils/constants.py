# Global constants for the benchmark engine

# Existing providers
from providers.openai_provider import call_openai
from providers.groq_provider import call_groq
from providers.together_provider import call_together
from providers.openrouter_provider import call_openrouter

# New providers (Phase 2 - OpenAI Compatible)
from providers.deepseek_provider import call_deepseek
from providers.cerebras_provider import call_cerebras
from providers.mistral_provider import call_mistral
from providers.fireworks_provider import call_fireworks
from providers.sambanova_provider import call_sambanova

# Phase 3 - Custom SDK Providers
from providers.anthropic_provider import call_anthropic
from providers.google_provider import call_google

BENCHMARK_PROMPT = """The history of timekeeping is a testament to humanity's obsession with measuring the passage of existence. Before the mechanical precision of modern clocks, early civilizations relied on the celestial bodies to organize their lives. The sun, moon, and stars provided the first canvas for tracking time. The Egyptians, for instance, constructed towering obelisks that cast shadows, effectively functioning as primitive sundials that divided the day into segments. However, these devices had a significant limitation: they were useless at night or on cloudy days.

To overcome the reliance on the sun, the Greeks and Romans refined the water clock, or clepsydra. These devices measured time by the regulated flow of water into or out of a vessel. While more consistent than sundials, they required constant maintenance to ensure the flow remained steady despite temperature changes affecting the water's viscosity. Simultaneously, in the East, incense clocks burned at a known rate, providing a scented measure of passing hours in temples and homes.

The true revolution occurred in medieval Europe with the invention of the mechanical escapement mechanism. This innovation allowed for the controlled release of energy from a falling weight, translating it into the rhythmic ticking sound we associate with clocks today. These early mechanical clocks, often installed in town towers, did not have faces or hands; they simply rang bells to signal the hour for prayer and work. They were the heartbeat of the medieval city, synchronizing the community's labor and worship.

By the 17th century, the pendulum clock, introduced by Christiaan Huygens, brought unprecedented accuracy, reducing the deviation from minutes per day to seconds. This leap forward enabled scientists to conduct more precise experiments and navigators to begin solving the problem of longitude at sea. The evolution continued with the shrinking of mechanisms into pocket watches and eventually wristwatches, democratizing time and strapping it to the individual's arm.

Today, we rely on atomic clocks, which measure time based on the vibration of cesium atoms. These devices are so accurate that they would lose less than a second in millions of years. This hyper-precision underpins the GPS technology that guides our cars and the internet protocols that synchronize our global communication networks. From the shadow of an obelisk to the vibration of an atom, the history of timekeeping is a journey from observing nature to mastering the fundamental forces of physics."""

PROVIDER_CONFIG = {
    # Existing providers
    "openai": {
        "display_name": "OpenAI",
        "base_url": "https://api.openai.com",
        "pricing_url": "https://platform.openai.com/docs/pricing",
    },
    "groq": {
        "display_name": "Groq",
        "base_url": "https://api.groq.com",
        "pricing_url": "https://groq.com/pricing",
    },
    "together": {
        "display_name": "Together AI",
        "base_url": "https://api.together.xyz",
        "models_url": "https://api.together.xyz/v1/models",
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "base_url": "https://openrouter.ai",
        "pricing_url": "https://openrouter.ai/api/v1/pricing/public",
    },
    # New providers (Phase 2)
    "deepseek": {
        "display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "pricing_url": "https://platform.deepseek.com/pricing",
    },
    "cerebras": {
        "display_name": "Cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "pricing_url": "https://cerebras.ai/pricing",
    },
    "mistral": {
        "display_name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "pricing_url": "https://mistral.ai/pricing",
    },
    "fireworks": {
        "display_name": "Fireworks AI",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "pricing_url": "https://fireworks.ai/pricing",
    },
    "sambanova": {
        "display_name": "SambaNova",
        "base_url": "https://api.sambanova.ai/v1",
        "pricing_url": "https://sambanova.ai/pricing",
    },
    # Phase 3 - Custom SDK Providers
    "anthropic": {
        "display_name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "pricing_url": "https://www.anthropic.com/pricing",
    },
    "google": {
        "display_name": "Google",
        "base_url": "https://generativelanguage.googleapis.com",
        "pricing_url": "https://ai.google.dev/pricing",
    },
}

PROVIDERS = [
    # Phase 0 - MVP (Existing providers with updates)
    # OpenAI - Industry standard
    ("openai", call_openai, "gpt-4o-mini"),                    # Baseline budget model
    ("openai", call_openai, "gpt-4o"),                         # Flagship
    ("openai", call_openai, "o1-preview"),                     # Reasoning model (requires Tier 5 access)
    
    # Groq - LPU benchmark (updated to latest)
    ("groq", call_groq, "llama-3.3-70b-versatile"),            # Latest Llama 3.3
    
    # Together AI - GPU cloud
    ("together", call_together, "mistralai/Mixtral-8x7B-Instruct-v0.1"),  # Existing
    ("together", call_together, "meta-llama/Llama-3.3-70B-Instruct-Turbo"),  # New - Infrastructure War
    
    # OpenRouter - Aggregator
    ("openrouter", call_openrouter, "openai/gpt-4o-mini"),     # Baseline
    ("openrouter", call_openrouter, "meta-llama/llama-3.3-70b-instruct"),  # Infrastructure War comparison
    ("openrouter", call_openrouter, "minimax/minimax-01"),     # Challenger to Claude
    
    # New providers (Phase 2 - OpenAI Compatible)
    # DeepSeek - Budget champion with disruptive pricing
    ("deepseek", call_deepseek, "deepseek-chat"),         # V3 - Budget model
    ("deepseek", call_deepseek, "deepseek-reasoner"),     # R1 - Reasoning model
    
    # Cerebras - Infrastructure War competitor (Groq challenger)
    ("cerebras", call_cerebras, "llama-3.3-70b"),
    
    # Mistral - European flagship
    ("mistral", call_mistral, "mistral-large-latest"),
    
    # Fireworks - Low latency on standard GPUs
    ("fireworks", call_fireworks, "accounts/fireworks/models/llama-v3p3-70b-instruct"),
    
    # SambaNova - Custom chip architecture
    ("sambanova", call_sambanova, "Meta-Llama-3.3-70B-Instruct"),
    
    # Phase 3 - Custom SDK Providers
    # Anthropic Claude - Developer favorite, high quality
    ("anthropic", call_anthropic, "claude-3-5-sonnet-latest"),  # Flagship (best quality)
    ("anthropic", call_anthropic, "claude-3-5-haiku-latest"),   # Budget (fast & cheap)
    
    # Google Gemini - NEW SDK with Gemini 2.5
    ("google", call_google, "models/gemini-2.5-pro"),       # Latest Pro - best quality
    ("google", call_google, "models/gemini-2.5-flash"),     # Latest Flash - fast & cheap
]
