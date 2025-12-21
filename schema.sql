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
    finished_at timestamptz
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

    created_at timestamptz not null default now()
);

-- Indexes for query performance
create index if not exists idx_providers_name on public.providers(name);
create index if not exists idx_models_provider_id on public.models(provider_id);
create index if not exists idx_models_name on public.models(name);
create index if not exists idx_prices_provider_id on public.prices(provider_id);
create index if not exists idx_prices_model_id on public.prices(model_id);
create index if not exists idx_prices_timestamp on public.prices(timestamp);
create index if not exists idx_benchmark_results_run_id on public.benchmark_results(run_id);
create index if not exists idx_benchmark_results_provider_id on public.benchmark_results(provider_id);
create index if not exists idx_benchmark_results_model_id on public.benchmark_results(model_id);
create index if not exists idx_benchmark_results_provider on public.benchmark_results(provider);
create index if not exists idx_benchmark_results_model on public.benchmark_results(model);
create index if not exists idx_benchmark_results_created_at on public.benchmark_results(created_at);
