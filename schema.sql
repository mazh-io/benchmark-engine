-- RUNS TABLE
-- Stores information about each benchmark execution session
create table if not exists public.runs (
    id uuid primary key default gen_random_uuid(),
    run_name text not null,
    triggered_by text not null,
    started_at timestamptz not null default now(),
    finished_at timestamptz
);

-- BENCHMARK RESULTS TABLE
-- Stores individual benchmark test results for each provider/model
create table if not exists public.benchmark_results (
    id uuid primary key default gen_random_uuid(), 
    run_id uuid not null references public.runs(id) on delete cascade,

    provider text not null,
    model text not null,

    input_tokens integer not null,
    output_tokens integer not null,
    latency_ms double precision not null,
    cost_usd double precision not null,

    success boolean not null default true,
    error_message text,
    response_text text,

    created_at timestamptz not null default now()
);

-- Indexes for query performance
create index if not exists idx_benchmark_results_run_id on public.benchmark_results(run_id);
create index if not exists idx_benchmark_results_provider on public.benchmark_results(provider);
create index if not exists idx_benchmark_results_model on public.benchmark_results(model);
