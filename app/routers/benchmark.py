"""
Benchmark Router

Endpoints for running benchmarks:
  - POST /api/benchmark/init       → Initialize a new benchmark queue
  - POST /api/benchmark/process    → Process a batch from the queue
  - POST /api/benchmark/run        → Trigger a full benchmark run (background)
  - GET  /api/benchmark/status     → Get queue stats for a run
"""

import traceback
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.dependencies import get_db, get_budget_breaker
from app.schemas import (
    BenchmarkInitResponse,
    BenchmarkBatchResponse,
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    ErrorResponse,
)

from benchmarking.queue_benchmark_runner import run_benchmark_batch, init_benchmark_queue
from benchmarking.benchmark_runner import run_benchmark
from database.base_db_client import BaseDatabaseClient

router = APIRouter(
    prefix="/api/benchmark",
    tags=["Benchmark"],
)


@router.post(
    "/init",
    response_model=BenchmarkInitResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Initialize benchmark queue",
    description="Create a new benchmark run and populate the queue with all provider/model combinations.",
)
def benchmark_init(
    run_name: str = Query(default="api-queue-run", description="Name of the run"),
    triggered_by: str = Query(default="api", description="Who triggered the run"),
):
    """Initialize a new benchmark run and populate the queue."""
    try:
        run_id = init_benchmark_queue(
            run_name=run_name,
            triggered_by=triggered_by,
        )

        if run_id:
            return BenchmarkInitResponse(
                status="success",
                message="Benchmark queue initialized",
                run_id=run_id,
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize benchmark queue",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/process",
    response_model=BenchmarkBatchResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Process benchmark batch",
    description="Process a batch of pending items from the benchmark queue.",
)
def benchmark_process(
    batch_size: int = Query(default=10, ge=1, le=50, description="Number of items to process"),
    db: BaseDatabaseClient = Depends(get_db),
):
    """Process a batch of benchmarks from the queue."""
    try:
        result = run_benchmark_batch(batch_size=batch_size)

        # Try to get queue stats
        queue_stats = None
        if result.get("processed", 0) > 0:
            pending_items = db.get_pending_queue_items(limit=1)
            if pending_items and len(pending_items) > 0:
                run_id = str(pending_items[0]["run_id"])
                queue_stats = db.get_queue_stats(run_id)

        return BenchmarkBatchResponse(
            status="success",
            message="Batch processed",
            result=result,
            queue_stats=queue_stats,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _run_benchmark_background(run_name: str, triggered_by: str, provider_filter: Optional[list] = None):
    """Background task wrapper for running a full benchmark."""
    try:
        run_benchmark(
            run_name=run_name,
            triggered_by=triggered_by,
            provider_filter=provider_filter,
        )
    except Exception as e:
        print(f"❌ Background benchmark failed: {e}")
        traceback.print_exc()


@router.post(
    "/run",
    response_model=BenchmarkRunResponse,
    summary="Run full benchmark (background)",
    description=(
        "Trigger a full benchmark run across all (or filtered) providers. "
        "Runs in the background — returns immediately."
    ),
)
def benchmark_run(
    body: BenchmarkRunRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger a full benchmark run as a background task."""
    background_tasks.add_task(
        _run_benchmark_background,
        run_name=body.run_name,
        triggered_by=body.triggered_by,
        provider_filter=body.provider_filter,
    )

    return BenchmarkRunResponse(
        status="accepted",
        message="Benchmark run started in background",
        run_name=body.run_name,
        triggered_by=body.triggered_by,
        provider_filter=body.provider_filter,
    )


@router.get(
    "/init",
    response_model=BenchmarkInitResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Initialize benchmark queue (GET, cron-friendly)",
    description=(
        "Synchronous GET endpoint for Vercel Cron. "
        "Creates a new run and populates the queue, then returns."
    ),
)
def benchmark_init_get(
    run_name: str = Query(default="vercel-queue-run", description="Name of the run"),
    triggered_by: str = Query(default="vercel-cron", description="Who triggered the run"),
):
    """Initialize benchmark queue (synchronous, for Vercel Cron)."""
    try:
        run_id = init_benchmark_queue(run_name=run_name, triggered_by=triggered_by)
        if run_id:
            return BenchmarkInitResponse(
                status="success",
                message="Benchmark queue initialized",
                run_id=run_id,
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize benchmark queue")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/process",
    response_model=BenchmarkBatchResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Process benchmark batch (GET, cron-friendly)",
    description=(
        "Synchronous GET endpoint for Vercel Cron. "
        "Processes a batch of pending queue items, then returns."
    ),
)
def benchmark_process_get(
    batch_size: int = Query(default=10, ge=1, le=50, description="Number of items to process"),
    db: BaseDatabaseClient = Depends(get_db),
):
    """Process benchmark batch (synchronous, for Vercel Cron)."""
    try:
        result = run_benchmark_batch(batch_size=batch_size)
        queue_stats = None
        if result.get("processed", 0) > 0:
            pending_items = db.get_pending_queue_items(limit=1)
            if pending_items and len(pending_items) > 0:
                run_id = str(pending_items[0]["run_id"])
                queue_stats = db.get_queue_stats(run_id)
        return BenchmarkBatchResponse(
            status="success",
            message="Batch processed",
            result=result,
            queue_stats=queue_stats,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status/{run_id}",
    summary="Get queue stats for a run",
    description="Returns pending/processing/completed/failed counts for a given run.",
)
def benchmark_status(
    run_id: str,
    db: BaseDatabaseClient = Depends(get_db),
):
    """Get queue statistics for a benchmark run."""
    try:
        stats = db.get_queue_stats(run_id)
        if stats is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        return {
            "status": "success",
            "run_id": run_id,
            "queue_stats": stats,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DIAGNOSTIC ENDPOINT — Direct provider test (bypasses queue & budget)
# ============================================================================

@router.get(
    "/debug/{provider_key}",
    summary="Debug: call a single provider directly",
    description=(
        "Bypasses the queue, budget check, and cron system entirely. "
        "Calls the provider function directly and returns the raw result. "
        "Use this to verify API keys, SDK availability, and model validity in Vercel."
    ),
)
def benchmark_debug_provider(
    provider_key: str,
    model: Optional[str] = Query(default=None, description="Model to test. If omitted, uses first active model for provider."),
):
    """Direct provider call for debugging — no queue, no budget, no DB save."""
    import os
    from utils.provider_service import get_provider_service, ACTIVE_MODELS
    from utils.constants import PROVIDER_CONFIG

    diagnostics = {
        "provider_key": provider_key,
        "model_requested": model,
        "env_checks": {},
        "provider_loaded": False,
        "call_result": None,
        "error": None,
    }

    # 1. Check if provider exists in PROVIDER_CONFIG
    if provider_key not in PROVIDER_CONFIG:
        diagnostics["error"] = f"Unknown provider: {provider_key}"
        return diagnostics

    # 2. Check relevant env vars
    env_key_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "together": "TOGETHER_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "fireworks": "FIREWORKS_API_KEY",
        "sambanova": "SAMBANOVA_API_KEY",
        "xai": "XAI_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "cohere": "CO_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    expected_key = env_key_map.get(provider_key, f"{provider_key.upper()}_API_KEY")
    key_value = os.getenv(expected_key)
    diagnostics["env_checks"][expected_key] = (
        f"SET ({len(key_value)} chars)" if key_value else "MISSING"
    )

    if not key_value:
        diagnostics["error"] = f"{expected_key} is not set in Vercel environment"
        return diagnostics

    # 3. Resolve model
    if not model:
        for prov, model_id, cat, notes in ACTIVE_MODELS:
            if prov == provider_key:
                model = model_id
                break
    if not model:
        diagnostics["error"] = f"No model specified and none found in ACTIVE_MODELS for {provider_key}"
        return diagnostics
    diagnostics["model_used"] = model

    # 4. Load provider function
    try:
        service = get_provider_service()
        call_fn = service.get_provider_function(provider_key)
        diagnostics["provider_loaded"] = True
    except Exception as e:
        diagnostics["error"] = f"Failed to load provider function: {e}"
        return diagnostics

    # 5. Call the provider directly with a short test prompt
    test_prompt = "Explain what an API is in two sentences."
    try:
        result = call_fn(test_prompt, model)
        diagnostics["call_result"] = {
            "success": result.get("success"),
            "status_code": result.get("status_code"),
            "error_message": result.get("error_message"),
            "error_type": result.get("error_type"),
            "input_tokens": result.get("input_tokens"),
            "output_tokens": result.get("output_tokens"),
            "total_latency_ms": result.get("total_latency_ms"),
            "ttft_ms": result.get("ttft_ms"),
            "cost_usd": result.get("cost_usd"),
            "response_preview": (result.get("response_text") or "")[:200],
        }
    except Exception as e:
        diagnostics["error"] = f"Provider call raised exception: {type(e).__name__}: {e}"
        diagnostics["traceback"] = traceback.format_exc()

    return diagnostics
