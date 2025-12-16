# Benchmark Engine

A lightweight MVP tool for benchmarking AI model providers. Test multiple providers sequentially, measure performance metrics (latency, tokens, cost), and store results in Supabase for analysis.

## Features

- **Multi-Provider Support**: Test OpenAI, Groq, Together AI, and OpenRouter
- **Performance Metrics**: Track latency, input/output tokens, and cost per request
- **Database Integration**: Store all benchmark results in Supabase with full history
- **Simple & Linear**: Sequential execution (no async complexity) - perfect for MVP
- **Error Handling**: Graceful failure handling with detailed error messages
- **UUID Tracking**: Each request gets a unique UUID for tracking and debugging
- **Response Storage**: Full AI responses stored for validation and analysis


## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd benchmark-engine
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirments.txt
   ```

## Configuration

1. **Create `.env` file** in the project root:
   ```env
   # Supabase
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE=your_service_role_key

   # Provider API Keys
   OPENAI_API_KEY=your_openai_key
   GROQ_API_KEY=your_groq_key
   TOGETHER_API_KEY=your_together_key
   OPENROUTER_API_KEY=your_openrouter_key
   ```

2. **Set up database**:
   - Create a Supabase project
   - Run `schema.sql` in your Supabase SQL editor to create the tables

## Usage

### Single Run

Run the benchmark once:

```bash
python main.py
```

### Scheduled Runs (Every 15 minutes for 4 hours)

Run continuously for 4 hours with 15-minute intervals:

```bash
python run_scheduled.py
```

This will execute 16 benchmark runs (4 hours × 60 minutes / 15 minutes).

### Cron Job Setup

For automated scheduling, use `cron_example.sh`:

1. **Make script executable:**
   ```bash
   chmod +x cron_example.sh
   ```

2. **Edit crontab:**
   ```bash
   crontab -e
   ```

3. **Add this line to run every 15 minutes:**
   ```cron
   */15 * * * * /full/path/to/benchmark-engine/cron_example.sh
   ```

   Or for a single run at specific times:
   ```cron
   0,15,30,45 * * * * /full/path/to/benchmark-engine/cron_example.sh
   ```

The script will:
1. Create a new benchmark run in the database
2. Test each provider sequentially with the configured prompt
3. Measure latency, tokens, and calculate costs
4. Save all results to Supabase (including full response text)
5. Print progress and results to console

### Example Output

```
Benchmark Engine – MVP

Starting benchmark run: mvp-validation-run
Triggered by: system

Run started: 766108b9-5a8e-4822-ae57-31de08cb0da3

Testing → openai / gpt-4o-mini
Success (openai)
   Latency: 5068.09 ms
   Tokens: 531 in / 103 out
   Cost: $0.000141
 Saved to DB
...
```

## Database Schema

### `runs`
Stores information about each benchmark execution session:
- `id` (UUID) - Primary key
- `run_name` (text) - Name of the run
- `triggered_by` (text) - Who triggered the run
- `started_at` (timestamp) - When the run started
- `finished_at` (timestamp) - When the run finished (nullable)

### `benchmark_results`
Stores individual benchmark test results for each provider/model:
- `id` (UUID) - Primary key
- `run_id` (UUID) - Foreign key to `runs` table
- `provider` (text) - Provider name (e.g. "openai", "groq")
- `model` (text) - Model name (e.g. "gpt-4o-mini")
- `input_tokens` (integer) - Number of input tokens
- `output_tokens` (integer) - Number of output tokens
- `latency_ms` (double precision) - Response time in milliseconds
- `cost_usd` (double precision) - Cost in USD
- `success` (boolean) - Whether the request succeeded
- `error_message` (text, nullable) - Error message if failed
- `response_text` (text, nullable) - Full AI response text
- `created_at` (timestamp) - When the result was created

## Supported Providers

| Provider | Default Model | Status |
|----------|--------------|--------|
| OpenAI | gpt-4o-mini |
| Groq | llama-3.1-8b-instant | 
| Together AI | mistralai/Mixtral-8x7B-Instruct-v0.1 | 
| OpenRouter | openai/gpt-4o-mini | 

## Customization

### Change Models

Edit `PROVIDERS` list in `src/benchmarking/benchmark_runner.py`:

```python
PROVIDERS = [
    ("openai", call_openai, "gpt-4o-mini"),
    ("groq", call_groq, "llama-3.1-8b-instant"),
    # Add or modify providers here
]
```

### Change Benchmark Prompt

Edit `BENCHMARK_PROMPT` in `src/benchmarking/benchmark_runner.py`.

### Pricing Updates

Update `PRICING` dictionaries in each provider file to reflect current pricing.

## Requirements

- Python 3.9+
- Supabase account
- API keys for providers you want to test

## License

MIT

## How It Works

1. **Run Creation**: Each execution creates a new `benchmark_runs` entry with a unique UUID
2. **Sequential Testing**: Providers are tested one after another (no async)
3. **Metrics Collection**: For each provider:
   - Latency is measured from API call start to response
   - Token counts are extracted from API response
   - Cost is calculated based on provider pricing tables
   - Full response text is stored for validation
4. **Database Storage**: All results are saved to Supabase with:
   - Run ID linking all benchmarks together
   - Success/failure status
   - Error messages for failed requests
   - Complete response text for successful requests

## Troubleshooting

### Common Issues

- **401 Unauthorized**: Check that your API keys are correct in `.env`
- **400 Bad Request**: Verify model names are correct for each provider
- **Database Errors**: Ensure Supabase credentials are correct and schema is applied

## Notes

This is an MVP (Minimum Viable Product) for market validation. The codebase prioritizes simplicity and speed over robust architecture. Perfect for validating the market need before investing in more complex infrastructure.
