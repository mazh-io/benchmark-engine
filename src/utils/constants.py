# Global constants for the benchmark engine

BENCHMARK_PROMPT = """The history of timekeeping is a testament to humanity's obsession with measuring the passage of existence. Before the mechanical precision of modern clocks, early civilizations relied on the celestial bodies to organize their lives. The sun, moon, and stars provided the first canvas for tracking time. The Egyptians, for instance, constructed towering obelisks that cast shadows, effectively functioning as primitive sundials that divided the day into segments. However, these devices had a significant limitation: they were useless at night or on cloudy days.

To overcome the reliance on the sun, the Greeks and Romans refined the water clock, or clepsydra. These devices measured time by the regulated flow of water into or out of a vessel. While more consistent than sundials, they required constant maintenance to ensure the flow remained steady despite temperature changes affecting the water's viscosity. Simultaneously, in the East, incense clocks burned at a known rate, providing a scented measure of passing hours in temples and homes.

The true revolution occurred in medieval Europe with the invention of the mechanical escapement mechanism. This innovation allowed for the controlled release of energy from a falling weight, translating it into the rhythmic ticking sound we associate with clocks today. These early mechanical clocks, often installed in town towers, did not have faces or hands; they simply rang bells to signal the hour for prayer and work. They were the heartbeat of the medieval city, synchronizing the community's labor and worship.

By the 17th century, the pendulum clock, introduced by Christiaan Huygens, brought unprecedented accuracy, reducing the deviation from minutes per day to seconds. This leap forward enabled scientists to conduct more precise experiments and navigators to begin solving the problem of longitude at sea. The evolution continued with the shrinking of mechanisms into pocket watches and eventually wristwatches, democratizing time and strapping it to the individual's arm.

Today, we rely on atomic clocks, which measure time based on the vibration of cesium atoms. These devices are so accurate that they would lose less than a second in millions of years. This hyper-precision underpins the GPS technology that guides our cars and the internet protocols that synchronize our global communication networks. From the shadow of an obelisk to the vibration of an atom, the history of timekeeping is a journey from observing nature to mastering the fundamental forces of physics."""

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

PROVIDERS = [
    ("openai", "call_openai", "gpt-4o-mini"),
    ("groq", "call_groq", "llama-3.1-8b-instant"),
    ("together", "call_together", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
    ("openrouter", "call_openrouter", "openai/gpt-4o-mini"),
]
