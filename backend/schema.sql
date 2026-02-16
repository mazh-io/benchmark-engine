-- PROVIDERS TABLE
-- Stores static information about AI providers (OpenAI, Groq, Together AI, etc.)
create table if not exists public.providers (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    base_url text,
    logo_url text,
    created_at timestamptz not null default now()
);

-- MODELS TABLE
-- Stores information about AI models (gpt-4o-mini, llama-3-70b-instruct, etc.)
create table if not exists public.models (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    provider_id uuid not null references public.providers(id) on delete cascade,
    context_window integer,
    active boolean not null default false,  -- TRUE if used in active benchmarks
    last_seen_at timestamptz not null default now(),  -- Last time model was discovered from API
    created_at timestamptz not null default now(),
    unique(name, provider_id)
);

-- PRICES TABLE (History Table)
-- Stores historical pricing data scraped from OpenRouter API
-- Updated daily to track price changes over time
create table if not exists public.prices (
    id uuid primary key default gen_random_uuid(),
    provider_id uuid not null references public.providers(id) on delete cascade,
    model_id uuid not null references public.models(id) on delete cascade,
    input_price_per_m double precision not null,
    output_price_per_m double precision not null,
    timestamp timestamptz not null default now()
);

-- RUNS TABLE
-- Stores information about each benchmark execution session
create table if not exists public.runs (
    id uuid primary key default gen_random_uuid(),
    run_name text not null,
    triggered_by text not null,
    started_at timestamptz not null default now(),
    finished_at timestamptz  -- NULL = running, NOT NULL = finished
);

-- BENCHMARK RESULTS TABLE (Time-Series Table)
-- Stores individual benchmark test results for each provider/model
-- Updated every 15 minutes via Performance Bot
create table if not exists public.benchmark_results (
    id uuid primary key default gen_random_uuid(), 
    run_id uuid not null references public.runs(id) on delete cascade,
    
    -- Foreign keys to providers and models tables
    provider_id uuid references public.providers(id) on delete set null,
    model_id uuid references public.models(id) on delete set null,
    
    -- Legacy text fields (for backward compatibility during migration)
    provider text,
    model text,

    -- Performance metrics
    input_tokens integer not null,
    output_tokens integer not null,
    reasoning_tokens integer,  -- Reasoning/thinking tokens (for models like DeepSeek R1, OpenAI o-series)
    total_latency_ms double precision not null,
    ttft_ms double precision,  -- Time to First Token (measured via streaming)
    tps double precision,     -- Tokens Per Second: (Total Tokens - 1) / (Time End - Time First Token)
    
    -- Status and error tracking
    status_code integer,       -- HTTP status code: 200, 500, 429, etc.
    success boolean not null default true,
    error_message text,
    response_text text,
    
    -- Cost calculation
    cost_usd double precision not null,
    
    -- Bang for Buck metric (Generated Column)
    -- Calculates tokens per dollar for cost efficiency comparison
    tokens_per_dollar double precision generated always as (
        case 
            when cost_usd > 0 then (input_tokens + output_tokens) / cost_usd
            else null
        end
    ) stored,

    created_at timestamptz not null default now()
);

-- RUN ERRORS TABLE
-- Stores errors that occur during benchmark runs
-- This table tracks all failures so we can monitor provider reliability
create table if not exists public.run_errors (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references public.runs(id) on delete cascade,
    
    -- Foreign keys to providers and models (nullable because error might occur before we identify these)
    provider_id uuid references public.providers(id) on delete set null,
    model_id uuid references public.models(id) on delete set null,
    
    -- Legacy text fields
    provider text,
    model text,
    
    -- Error details
    error_type text not null,  -- e.g., "RATE_LIMIT", "AUTH_ERROR", "TIMEOUT", "UNKNOWN_ERROR"
    error_message text not null,
    status_code integer,       -- HTTP status code if available
    
    -- Timing
    timestamp timestamptz not null default now()
);

-- BENCHMARK QUEUE TABLE
-- Queue system for processing benchmarks in batches to avoid timeouts
-- Each queue item represents one provider+model combination to test
create table if not exists public.benchmark_queue (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references public.runs(id) on delete cascade,
    
    -- Provider and model to test
    provider_key text not null,  -- e.g., "openai", "groq"
    model_name text not null,
    
    -- Queue status
    status text not null default 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    attempts integer not null default 0,     -- Number of processing attempts
    max_attempts integer not null default 3,  -- Maximum retry attempts
    
    -- Error tracking (for failed items)
    error_message text,
    
    -- Timing
    created_at timestamptz not null default now(),
    started_at timestamptz,     -- When processing started
    completed_at timestamptz,   -- When completed or failed
    
    -- Ensure no duplicates in same run
    unique(run_id, provider_key, model_name)
);

-- Indexes for query performance
create index if not exists idx_providers_name on public.providers(name);
create index if not exists idx_models_provider_id on public.models(provider_id);
create index if not exists idx_models_name on public.models(name);
create index if not exists idx_models_active on public.models(active);
create index if not exists idx_models_last_seen on public.models(last_seen_at);
create index if not exists idx_prices_provider_id on public.prices(provider_id);
create index if not exists idx_prices_model_id on public.prices(model_id);
create index if not exists idx_prices_timestamp on public.prices(timestamp);
create index if not exists idx_benchmark_results_run_id on public.benchmark_results(run_id);
create index if not exists idx_benchmark_results_provider_id on public.benchmark_results(provider_id);
create index if not exists idx_benchmark_results_model_id on public.benchmark_results(model_id);
create index if not exists idx_benchmark_results_provider on public.benchmark_results(provider);
create index if not exists idx_benchmark_results_model on public.benchmark_results(model);
create index if not exists idx_benchmark_results_created_at on public.benchmark_results(created_at);
create index if not exists idx_benchmark_results_tokens_per_dollar on public.benchmark_results(tokens_per_dollar);
create index if not exists idx_run_errors_run_id on public.run_errors(run_id);
create index if not exists idx_run_errors_provider_id on public.run_errors(provider_id);
create index if not exists idx_run_errors_error_type on public.run_errors(error_type);
create index if not exists idx_run_errors_timestamp on public.run_errors(timestamp);
create index if not exists idx_benchmark_queue_run_id on public.benchmark_queue(run_id);
create index if not exists idx_benchmark_queue_status on public.benchmark_queue(status);
create index if not exists idx_benchmark_queue_created_at on public.benchmark_queue(created_at);
