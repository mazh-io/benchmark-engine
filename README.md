# Benchmark Engine

A lightweight MVP tool for benchmarking AI model providers. Test multiple providers sequentially, measure performance metrics (latency, tokens, cost), and store results in Supabase for analysis.

## Features

- **Multi-Provider Support**: Test OpenAI, Groq, Together AI, and OpenRouter
- **Advanced Performance Metrics**: 
  - **Total Latency**: Complete request-to-response time
  - **TTFT (Time to First Token)**: Measures how quickly the first token arrives (via streaming)
  - **TPS (Tokens Per Second)**: Calculates token generation speed
  - **Status Codes**: HTTP status tracking (200, 500, 429, etc.)
- **Streaming Support**: All providers use streaming for accurate TTFT and TPS measurement
- **Database Integration**: Store all benchmark results in Supabase with full history
- **Simple & Linear**: Sequential execution (no async complexity) - perfect for MVP
- **Error Handling**: Graceful failure handling with detailed error messages and logging
- **Error Logging**: Automatic logging to `logs/` directory for debugging
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

This will:
1. Populate the `prices` table with current pricing data
2. Execute benchmarks for all configured providers
3. Save results to the database

### Cron Job Setup

For automated scheduling (e.g., every 15 minutes), use `cron_example.sh`:

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
✅ Success (openai)
   Total Latency: 4412.03 ms
   TTFT: 871.24 ms
   TPS: 30.50 tokens/sec
   Tokens: 520 in / 109 out
   Cost: $0.000143
   Status: 200
 Saved to DB

Testing → groq / llama-3.1-8b-instant
✅ Success (groq)
   Total Latency: 2612.43 ms
   TTFT: 2395.38 ms
   TPS: 700.32 tokens/sec
   Tokens: 520 in / 153 out
   Cost: $0.000038
   Status: 200
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
- `total_latency_ms` (double precision) - Total response time in milliseconds
- `ttft_ms` (double precision, nullable) - Time to First Token in milliseconds (measured via streaming)
- `tps` (double precision, nullable) - Tokens Per Second: (Total Tokens - 1) / (Time End - Time First Token)
- `status_code` (integer, nullable) - HTTP status code (200, 500, 429, etc.)
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

1. **Run Creation**: Each execution creates a new `runs` entry with a unique UUID
2. **Sequential Testing**: Providers are tested one after another (no async)
3. **Streaming & Metrics Collection**: For each provider:
   - **Streaming**: All providers use streaming to measure TTFT accurately
   - **Total Latency**: Measured from API call start to complete response
   - **TTFT (Time to First Token)**: Measured when first token arrives via streaming
   - **TPS (Tokens Per Second)**: Calculated as (Total Tokens - 1) / (Time End - Time First Token)
   - **Status Code**: HTTP status code captured (200, 500, 429, etc.)
   - **Token counts**: Extracted from API response
   - **Cost**: Calculated based on provider pricing tables
   - **Full response text**: Stored for validation
4. **Database Storage**: All results are saved to Supabase with:
   - Run ID linking all benchmarks together
   - All performance metrics (total_latency_ms, ttft_ms, tps, status_code)
   - Success/failure status
   - Error messages for failed requests
   - Complete response text for successful requests
5. **Error Logging**: All errors are automatically logged to `logs/benchmark_engine_YYYYMMDD.log`

## Testing

### Quick Test

Test a single provider quickly:

```bash
python3 test_single_provider.py
```

This will test all providers with a shorter prompt and display results including TTFT and TPS.

## Troubleshooting

### Common Issues

- **401 Unauthorized**: Check that your API keys are correct in `.env`
- **400 Bad Request**: Verify model names are correct for each provider
- **Database Errors**: Ensure Supabase credentials are correct and schema is applied
- **TTFT/TPS showing None**: This may happen if streaming fails or first token isn't detected. Check provider API status.
- **Logs not appearing**: Ensure `logs/` directory exists and has write permissions

### Check Logs

All errors are logged to `logs/benchmark_engine_YYYYMMDD.log`. Check this file for detailed error information.

## Notes

This is an MVP (Minimum Viable Product) for market validation. The codebase prioritizes simplicity and speed over robust architecture. Perfect for validating the market need before investing in more complex infrastructure.
