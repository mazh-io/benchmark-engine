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
from utils.budget_breaker import BudgetCircuitBreaker

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
