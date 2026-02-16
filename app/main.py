"""
Benchmark Engine – FastAPI Application

Main application factory. Creates the FastAPI app, registers routers,
and configures middleware, CORS, and the scheduler.
"""

import sys
import os
from contextlib import asynccontextmanager

# Add src folder to path BEFORE any other imports that depend on it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import benchmark, pricing, sync
from app.scheduler import start_scheduler, shutdown_scheduler, get_scheduler_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Startup: initializes the APScheduler for cron jobs.
    Shutdown: gracefully stops the scheduler.
    """
    # --- Startup ---
    start_scheduler()
    print("✅ Benchmark Engine API started")
    
    yield
    
    # --- Shutdown ---
    shutdown_scheduler()
    print("🛑 Benchmark Engine API stopped")


def create_app() -> FastAPI:
    """
    Application factory. Returns a fully configured FastAPI instance.
    """
    app = FastAPI(
        title="Benchmark Engine API",
        description=(
            "Production-ready API for benchmarking AI model providers. "
            "Test multiple providers, measure performance metrics (latency, TTFT, TPS, cost), "
            "scrape pricing data, and sync available models."
        ),
        version="2.0.0",
        lifespan=lifespan,
    )

    # ----- CORS -----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----- Routers -----
    app.include_router(benchmark.router)
    app.include_router(pricing.router)
    app.include_router(sync.router)

    # ----- Root health check -----
    @app.get("/", tags=["Health"])
    def health_check():
        return {
            "status": "healthy",
            "service": "benchmark-engine",
            "version": "2.0.0",
        }

    # ----- Scheduler status -----
    @app.get("/api/scheduler/status", tags=["Scheduler"])
    def scheduler_status():
        """Check which cron jobs are scheduled and when they fire next."""
        return get_scheduler_status()

    return app


# Create the app instance (used by uvicorn)
app = create_app()
