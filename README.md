# Benchmark Engine

A production-ready Python tool for benchmarking AI model providers. Test multiple providers sequentially, measure advanced performance metrics (latency, TTFT, TPS, cost), and store results in Supabase PostgreSQL database for comprehensive analysis.

## Overview

The Benchmark Engine is designed to continuously monitor and compare AI inference performance across multiple providers. It acts as a "mystery shopper" that tests real API endpoints, measures critical performance metrics, and maintains a historical database of results for trend analysis.

### Key Capabilities

- **Multi-Provider Testing**: Supports OpenAI, Groq, Together AI, and OpenRouter
- **Advanced Metrics**: Total latency, TTFT (Time to First Token), TPS (Tokens Per Second), HTTP status codes
- **Streaming Support**: All providers use streaming for accurate real-time metrics
- **Database Normalization**: Proper relational schema with foreign keys and indexes
- **Historical Tracking**: Complete audit trail of all benchmark runs and pricing changes
- **Error Resilience**: Graceful error handling with comprehensive logging

## Features

- **Multi-Provider Support**: Test OpenAI, Groq, Together AI, and OpenRouter
- **Advanced Performance Metrics**: 
  - **Total Latency**: Complete request-to-response time
  - **TTFT (Time to First Token)**: Measures how quickly the first token arrives (via streaming)
  - **TPS (Tokens Per Second)**: Calculates token generation speed
  - **Status Codes**: HTTP status tracking (200, 500, 429, etc.)
- **Streaming Support**: All providers use streaming for accurate TTFT and TPS measurement
- **Database Integration**: Store all benchmark results in Supabase with full history
- **Automatic Model Discovery**: Weekly sync of available models from provider APIs
  - Fetches models from each provider's API automatically
  - Tracks active models (used in benchmarks) vs available models
  - Runs via Vercel cron every Sunday at 2 AM UTC
  - Manual sync available: `python scripts/sync_models.py`
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
   pip install -r requirements.txt
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
   - Create a Supabase project at [supabase.com](https://supabase.com)
   - Go to SQL Editor in your Supabase dashboard
   - Copy and paste the contents of `schema.sql`
   - Execute the SQL to create all tables and indexes
   - Verify tables are created: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`

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

The database uses PostgreSQL (via Supabase) with a normalized relational schema. All tables use UUID primary keys for scalability and include timestamps for audit trails.

### Schema Overview

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  providers  │◄────────┤   models   │◄────────┤   prices    │
│             │         │             │         │  (history)  │
└─────────────┘         └─────────────┘         └─────────────┘
      ▲                        ▲                       
      │                        │                       
      │                        │                       
┌─────────────┐         ┌─────────────┐               
│    runs     │         │ benchmark_  │               
│             │◄────────┤  results    │               
└─────────────┘         └─────────────┘               
```

### Table: `providers`

Stores static information about AI providers (OpenAI, Groq, Together AI, etc.). This is a reference table that rarely changes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PRIMARY KEY, DEFAULT `gen_random_uuid()` | Unique identifier for the provider |
| `name` | `text` | NOT NULL, UNIQUE | Display name (e.g., "OpenAI", "Groq") |
| `base_url` | `text` | NULLABLE | Base API URL (e.g., "https://api.openai.com") |
| `logo_url` | `text` | NULLABLE | URL to provider logo for UI display |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT `now()` | When the provider was first added |

**Indexes:**
- `idx_providers_name` on `name` - Fast lookup by provider name

**Usage Example:**
```sql
-- Get all providers
SELECT * FROM providers ORDER BY name;

-- Get provider by name
SELECT * FROM providers WHERE name = 'OpenAI';
```

### Table: `models`

Stores information about AI models. Each model belongs to exactly one provider (enforced by foreign key).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PRIMARY KEY, DEFAULT `gen_random_uuid()` | Unique identifier for the model |
| `name` | `text` | NOT NULL | Model identifier (e.g., "gpt-4o-mini", "llama-3.1-8b-instant") |
| `provider_id` | `uuid` | NOT NULL, FOREIGN KEY → `providers(id)` ON DELETE CASCADE | Reference to the provider |
| `context_window` | `integer` | NULLABLE | Context window size in tokens (e.g., 8192, 32768) |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT `now()` | When the model was first added |

**Constraints:**
- `UNIQUE(name, provider_id)` - Ensures no duplicate model names per provider
- `ON DELETE CASCADE` - If a provider is deleted, all its models are automatically deleted

**Indexes:**
- `idx_models_provider_id` on `provider_id` - Fast joins with providers
- `idx_models_name` on `name` - Fast lookup by model name

**Usage Example:**
```sql
-- Get all models with their provider names
SELECT m.*, p.name as provider_name 
FROM models m 
JOIN providers p ON m.provider_id = p.id;

-- Get models for a specific provider
SELECT * FROM models WHERE provider_id = (
    SELECT id FROM providers WHERE name = 'OpenAI'
);
```

### Table: `prices` (History Table)

Stores historical pricing data. This is a time-series table that tracks price changes over time. Each row represents a price snapshot at a specific timestamp.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PRIMARY KEY, DEFAULT `gen_random_uuid()` | Unique identifier for the price record |
| `provider_id` | `uuid` | NOT NULL, FOREIGN KEY → `providers(id)` ON DELETE CASCADE | Reference to the provider |
| `model_id` | `uuid` | NOT NULL, FOREIGN KEY → `models(id)` ON DELETE CASCADE | Reference to the model |
| `input_price_per_m` | `double precision` | NOT NULL | Input price per 1 million tokens (USD) |
| `output_price_per_m` | `double precision` | NOT NULL | Output price per 1 million tokens (USD) |
| `timestamp` | `timestamptz` | NOT NULL, DEFAULT `now()` | When this price was recorded |

**Constraints:**
- `ON DELETE CASCADE` - If provider/model is deleted, price history is deleted

**Indexes:**
- `idx_prices_provider_id` on `provider_id` - Fast filtering by provider
- `idx_prices_model_id` on `model_id` - Fast filtering by model
- `idx_prices_timestamp` on `timestamp` - Fast time-range queries

**Usage Example:**
```sql
-- Get latest price for a specific model
SELECT * FROM prices 
WHERE model_id = '...' 
ORDER BY timestamp DESC 
LIMIT 1;

-- Get price history for a model (last 30 days)
SELECT * FROM prices 
WHERE model_id = '...' 
  AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;

-- Compare prices across providers for the same model type
SELECT p.name as provider, pr.input_price_per_m, pr.output_price_per_m, pr.timestamp
FROM prices pr
JOIN providers p ON pr.provider_id = p.id
JOIN models m ON pr.model_id = m.id
WHERE m.name LIKE '%gpt-4o-mini%'
ORDER BY pr.timestamp DESC, p.name;
```

### Table: `runs`

Stores information about each benchmark execution session. Each run represents one complete benchmark cycle that tests all configured providers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PRIMARY KEY, DEFAULT `gen_random_uuid()` | Unique identifier for the run |
| `run_name` | `text` | NOT NULL | Descriptive name (e.g., "mvp-validation-run", "scheduled-run-1") |
| `triggered_by` | `text` | NOT NULL | Who/what triggered the run (e.g., "system", "cron-job", "manual") |
| `started_at` | `timestamptz` | NOT NULL, DEFAULT `now()` | When the run started |
| `finished_at` | `timestamptz` | NULLABLE | When the run completed (NULL if still running) |

**Usage Example:**
```sql
-- Get all completed runs
SELECT * FROM runs WHERE finished_at IS NOT NULL ORDER BY started_at DESC;

-- Get run duration
SELECT 
    id,
    run_name,
    started_at,
    finished_at,
    finished_at - started_at as duration
FROM runs 
WHERE finished_at IS NOT NULL;

-- Get runs from the last 24 hours
SELECT * FROM runs 
WHERE started_at >= NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;
```

### Table: `benchmark_results` (Time-Series Table)

Stores individual benchmark test results. This is the core time-series table that grows continuously as benchmarks run. Each row represents one provider/model test within a run.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PRIMARY KEY, DEFAULT `gen_random_uuid()` | Unique identifier for the result |
| `run_id` | `uuid` | NOT NULL, FOREIGN KEY → `runs(id)` ON DELETE CASCADE | Reference to the run |
| `provider_id` | `uuid` | NULLABLE, FOREIGN KEY → `providers(id)` ON DELETE SET NULL | Reference to the provider (normalized) |
| `model_id` | `uuid` | NULLABLE, FOREIGN KEY → `models(id)` ON DELETE SET NULL | Reference to the model (normalized) |
| `provider` | `text` | NULLABLE | Legacy provider name (e.g., "openai") - for backward compatibility |
| `model` | `text` | NULLABLE | Legacy model name (e.g., "gpt-4o-mini") - for backward compatibility |
| `input_tokens` | `integer` | NOT NULL | Number of input tokens consumed |
| `output_tokens` | `integer` | NOT NULL | Number of output tokens generated |
| `total_latency_ms` | `double precision` | NOT NULL | Total request-to-response time in milliseconds |
| `ttft_ms` | `double precision` | NULLABLE | Time to First Token in milliseconds (measured via streaming) |
| `tps` | `double precision` | NULLABLE | Tokens Per Second: `(output_tokens - 1) / (end_time - first_token_time)` |
| `status_code` | `integer` | NULLABLE | HTTP status code (200 = success, 500 = server error, 429 = rate limit, etc.) |
| `success` | `boolean` | NOT NULL, DEFAULT `true` | Whether the request succeeded |
| `error_message` | `text` | NULLABLE | Error message if the request failed |
| `response_text` | `text` | NULLABLE | Full AI response text (for validation and analysis) |
| `cost_usd` | `double precision` | NOT NULL | Calculated cost in USD based on pricing |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT `now()` | When the result was recorded |

**Constraints:**
- `ON DELETE CASCADE` for `run_id` - If a run is deleted, all its results are deleted
- `ON DELETE SET NULL` for `provider_id`/`model_id` - If provider/model is deleted, results remain but foreign keys are set to NULL

**Indexes:**
- `idx_benchmark_results_run_id` on `run_id` - Fast filtering by run
- `idx_benchmark_results_provider_id` on `provider_id` - Fast filtering by provider (normalized)
- `idx_benchmark_results_model_id` on `model_id` - Fast filtering by model (normalized)
- `idx_benchmark_results_provider` on `provider` - Fast filtering by provider (legacy)
- `idx_benchmark_results_model` on `model` - Fast filtering by model (legacy)
- `idx_benchmark_results_created_at` on `created_at` - Fast time-range queries

**Usage Example:**
```sql
-- Get all results for a specific run
SELECT * FROM benchmark_results WHERE run_id = '...' ORDER BY created_at;

-- Get average latency by provider (last 24 hours)
SELECT 
    p.name as provider,
    AVG(br.total_latency_ms) as avg_latency_ms,
    AVG(br.ttft_ms) as avg_ttft_ms,
    AVG(br.tps) as avg_tps,
    COUNT(*) as test_count
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
WHERE br.created_at >= NOW() - INTERVAL '24 hours'
  AND br.success = true
GROUP BY p.name
ORDER BY avg_latency_ms;

-- Get performance trends over time
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    AVG(total_latency_ms) as avg_latency,
    AVG(ttft_ms) as avg_ttft,
    AVG(tps) as avg_tps,
    COUNT(*) as test_count
FROM benchmark_results
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND success = true
GROUP BY hour
ORDER BY hour DESC;

-- Get error rate by provider
SELECT 
    p.name as provider,
    COUNT(*) FILTER (WHERE success = false) as error_count,
    COUNT(*) as total_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE success = false) / COUNT(*), 2) as error_rate_percent
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY p.name
ORDER BY error_rate_percent DESC;

-- Get cost analysis
SELECT 
    p.name as provider,
    m.name as model,
    SUM(cost_usd) as total_cost,
    AVG(cost_usd) as avg_cost_per_request,
    COUNT(*) as request_count
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
JOIN models m ON br.model_id = m.id
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND success = true
GROUP BY p.name, m.name
ORDER BY total_cost DESC;
```

### Database Relationships

1. **providers → models**: One-to-Many (one provider has many models)
2. **providers → prices**: One-to-Many (one provider has many price records over time)
3. **models → prices**: One-to-Many (one model has many price records over time)
4. **runs → benchmark_results**: One-to-Many (one run has many benchmark results)
5. **providers → benchmark_results**: One-to-Many (one provider has many benchmark results)
6. **models → benchmark_results**: One-to-Many (one model has many benchmark results)

### Database Design Principles

1. **Normalization**: Providers and models are stored in separate tables to avoid duplication
2. **Foreign Keys**: Enforce referential integrity and enable JOIN queries
3. **UUID Primary Keys**: Scalable, globally unique identifiers
4. **Timestamps**: All tables include `created_at` for audit trails
5. **Indexes**: Strategic indexes on foreign keys and frequently queried columns
6. **Cascade Deletes**: Automatic cleanup when parent records are deleted
7. **Nullable Foreign Keys**: `provider_id` and `model_id` in `benchmark_results` are nullable to preserve historical data even if provider/model is deleted

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

Edit `BENCHMARK_PROMPT` in `src/utils/constants.py`:

```python
BENCHMARK_PROMPT = """Your custom prompt here..."""
```

### Pricing Updates

Pricing is hardcoded in each provider file's `PRICING` dictionary. Update these values to reflect current pricing:

- `src/providers/openai_provider.py`
- `src/providers/groq_provider.py`
- `src/providers/together_provider.py`
- `src/providers/openrouter_provider.py`

**Note**: For production, consider implementing automatic pricing updates from OpenRouter API or provider pricing pages.

## Requirements

- Python 3.9+
- Supabase account
- API keys for providers you want to test

## License

MIT

## Architecture

### Project Structure

```
benchmark-engine/
├── src/
│   ├── benchmarking/
│   │   ├── benchmark_runner.py    # Main orchestration logic
│   │   └── run_manager.py          # Run lifecycle management
│   ├── database/
│   │   └── supabase_client.py     # Database operations (CRUD)
│   ├── providers/
│   │   ├── openai_provider.py     # OpenAI API integration
│   │   ├── groq_provider.py       # Groq API integration
│   │   ├── together_provider.py   # Together AI API integration
│   │   └── openrouter_provider.py # OpenRouter API integration
│   └── utils/
│       ├── constants.py            # Global constants (prompts, configs)
│       ├── env_helper.py           # Environment variable management
│       └── logger.py               # Logging utilities
├── api/
│   ├── benchmark.py                # API endpoint (if needed)
│   └── pricing_scraper.py          # Pricing scraper (if needed)
├── logs/                           # Log files (auto-generated)
├── main.py                         # Entry point
├── schema.sql                      # Database schema
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

### Code Architecture

#### 1. **Entry Point** (`main.py`)
- Simple entry point that calls `run_benchmark()`
- Can be executed directly or via cron job

#### 2. **Benchmark Runner** (`src/benchmarking/benchmark_runner.py`)
- **Core orchestration logic**: Manages the entire benchmark execution flow
- **Sequential execution**: Tests providers one after another (no async complexity)
- **Database integration**: Automatically creates/retrieves providers and models
- **Result aggregation**: Collects and saves all benchmark results

**Key Functions:**
- `run_benchmark(run_name, triggered_by)`: Main entry point that executes the full benchmark cycle

**Process Flow:**
1. Creates a new run in the database via `RunManager`
2. Iterates through all configured providers
3. For each provider:
   - Gets or creates provider record in database
   - Gets or creates model record in database
   - Calls provider function with benchmark prompt
   - Collects performance metrics (latency, TTFT, TPS, tokens, cost)
   - Saves results to database
4. Marks run as finished

#### 3. **Run Manager** (`src/benchmarking/run_manager.py`)
- **Wrapper class**: Encapsulates run lifecycle management
- **Methods**:
  - `start()`: Creates a new run in database and stores UUID
  - `end()`: Marks run as finished with timestamp

#### 4. **Database Client** (`src/database/supabase_client.py`)
- **Centralized database operations**: All Supabase interactions go through this module
- **Functions organized by domain**:
  - **Runs**: `create_run()`, `finish_run()`, `get_all_runs()`
  - **Benchmark Results**: `save_benchmark()`, `get_all_benchmark_results()`, `get_benchmark_results_by_run_id()`
  - **Providers**: `get_or_create_provider()`, `get_all_providers()`
  - **Models**: `get_or_create_model()`, `get_all_models()`
  - **Prices**: `save_price()`, `get_latest_prices()`, `get_last_price_timestamp()`

**Design Pattern**: Uses "get or create" pattern to ensure data consistency and avoid duplicates.

#### 5. **Provider Modules** (`src/providers/*.py`)
Each provider module follows the same interface:

```python
def call_<provider>(prompt: str, model: str) -> dict:
    """
    Returns:
        {
            "input_tokens": int,
            "output_tokens": int,
            "total_latency_ms": float,
            "ttft_ms": float | None,
            "tps": float | None,
            "status_code": int,
            "cost_usd": float,
            "success": bool,
            "error_message": str | None,
            "response_text": str | None
        }
    """
```

**Common Implementation Pattern:**
1. Load API key from environment
2. Generate unique UUID for request tracking
3. Start timing
4. Make streaming API call
5. Measure TTFT when first token arrives
6. Collect all tokens and measure TPS
7. Calculate total latency
8. Extract token counts from API response
9. Calculate cost based on pricing table
10. Return standardized result dictionary

**Streaming Implementation:**
- All providers use streaming (`stream=True`) for accurate TTFT measurement
- First token arrival time is captured immediately
- Full response is collected chunk by chunk
- TPS is calculated as: `(output_tokens - 1) / (end_time - first_token_time)`

#### 6. **Constants** (`src/utils/constants.py`)
- **Centralized configuration**: All prompts, provider configs, and provider list
- **BENCHMARK_PROMPT**: The standard text used for all benchmarks
- **PROVIDER_CONFIG**: Mapping of provider names to display names and URLs
- **PROVIDERS**: List of tuples `(provider_name, function, model_name)` defining what to test

#### 7. **Utilities**
- **`env_helper.py`**: Centralized environment variable loading (works with `.env` files and production)
- **`logger.py`**: Structured logging to both file and console with context support

### Data Flow

```
┌─────────────┐
│   main.py   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ benchmark_runner.py │
│  - Creates Run      │
│  - Iterates Providers│
└──────┬──────────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Provider     │  │ Database     │
│ Functions    │  │ Client       │
│ (API calls)  │  │ (CRUD ops)   │
└──────────────┘  └──────────────┘
       │                 │
       │                 │
       └────────┬────────┘
                │
                ▼
         ┌──────────────┐
         │  Supabase    │
         │  PostgreSQL  │
         └──────────────┘
```

### How It Works

1. **Run Creation**: Each execution creates a new `runs` entry with a unique UUID
2. **Sequential Testing**: Providers are tested one after another (no async complexity)
3. **Streaming & Metrics Collection**: For each provider:
   - **Streaming**: All providers use streaming to measure TTFT accurately
   - **Total Latency**: Measured from API call start to complete response
   - **TTFT (Time to First Token)**: Measured when first token arrives via streaming
   - **TPS (Tokens Per Second)**: Calculated as `(output_tokens - 1) / (end_time - first_token_time)`
   - **Status Code**: HTTP status code captured (200, 500, 429, etc.)
   - **Token counts**: Extracted from API response or estimated from streaming chunks
   - **Cost**: Calculated based on provider pricing tables
   - **Full response text**: Stored for validation and analysis
4. **Database Storage**: All results are saved to Supabase with:
   - Run ID linking all benchmarks together
   - Provider and model foreign keys (normalized)
   - All performance metrics (total_latency_ms, ttft_ms, tps, status_code)
   - Success/failure status
   - Error messages for failed requests
   - Complete response text for successful requests
5. **Error Logging**: All errors are automatically logged to `logs/benchmark_engine_YYYYMMDD.log` with context

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

## Querying the Database

### Common Queries

#### Get all benchmark results
```sql
SELECT * FROM benchmark_results ORDER BY created_at DESC;
```

#### Get results for a specific run
```sql
SELECT * FROM benchmark_results WHERE run_id = 'your-run-uuid';
```

#### Get average performance by provider (last 24 hours)
```sql
SELECT 
    p.name as provider,
    m.name as model,
    AVG(br.total_latency_ms) as avg_latency_ms,
    AVG(br.ttft_ms) as avg_ttft_ms,
    AVG(br.tps) as avg_tps,
    COUNT(*) as test_count
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
JOIN models m ON br.model_id = m.id
WHERE br.created_at >= NOW() - INTERVAL '24 hours'
  AND br.success = true
GROUP BY p.name, m.name
ORDER BY avg_latency_ms;
```

#### Get latest prices for all models
```sql
SELECT DISTINCT ON (m.id)
    p.name as provider,
    m.name as model,
    pr.input_price_per_m,
    pr.output_price_per_m,
    pr.timestamp
FROM prices pr
JOIN providers p ON pr.provider_id = p.id
JOIN models m ON pr.model_id = m.id
ORDER BY m.id, pr.timestamp DESC;
```

#### Get error rate by provider
```sql
SELECT 
    p.name as provider,
    COUNT(*) FILTER (WHERE br.success = false) as errors,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE br.success = false) / COUNT(*), 2) as error_rate_pct
FROM benchmark_results br
JOIN providers p ON br.provider_id = p.id
WHERE br.created_at >= NOW() - INTERVAL '7 days'
GROUP BY p.name
ORDER BY error_rate_pct DESC;
```

### Using Supabase Dashboard

1. Navigate to **Table Editor** in your Supabase dashboard
2. Select any table to view data
3. Use **SQL Editor** for complex queries
4. Use **Database** → **Tables** to view schema and relationships

## Performance Considerations

### Database Indexes

All foreign keys and frequently queried columns are indexed for optimal performance:
- Foreign key columns (`run_id`, `provider_id`, `model_id`)
- Timestamp columns (`created_at`, `timestamp`)
- Name columns for lookups (`providers.name`, `models.name`)

### Query Optimization Tips

1. **Use indexes**: Always filter by indexed columns when possible
2. **Limit results**: Use `LIMIT` for large result sets
3. **Time ranges**: Filter by `created_at` for time-series queries
4. **JOINs**: Use proper JOINs instead of subqueries when possible

## Notes

This is a production-ready MVP designed for continuous monitoring of AI inference performance. The codebase prioritizes:
- **Simplicity**: Linear, sequential execution (no async complexity)
- **Reliability**: Comprehensive error handling and logging
- **Scalability**: Normalized database schema with proper indexes
- **Maintainability**: Clean separation of concerns and modular design

Perfect for validating market need and scaling to production workloads.
