"""
Pydantic models (schemas) for request/response validation.

FastAPI uses these to auto-validate input and auto-generate API docs.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ============================================================================
# Benchmark Schemas
# ============================================================================

class BenchmarkInitResponse(BaseModel):
    """Response when initializing a new benchmark queue."""
    status: str
    message: str
    run_id: Optional[str] = None


class BenchmarkBatchResponse(BaseModel):
    """Response after processing a batch of benchmarks."""
    status: str
    message: str
    result: Dict[str, Any]
    queue_stats: Optional[Dict[str, Any]] = None


class BenchmarkRunRequest(BaseModel):
    """Request body for triggering a full benchmark run."""
    run_name: str = Field(default="api-run", description="Name of the benchmark run")
    triggered_by: str = Field(default="api", description="Who triggered the run")
    provider_filter: Optional[List[str]] = Field(
        default=None,
        description="Optional list of provider keys to test (e.g., ['openai', 'groq'])"
    )


class BenchmarkRunResponse(BaseModel):
    """Response after triggering a full benchmark run."""
    status: str
    message: str
    run_name: str
    triggered_by: str
    provider_filter: Optional[List[str]] = None


# ============================================================================
# Pricing Scraper Schemas
# ============================================================================

class PricingScraperRequest(BaseModel):
    """Request body for triggering the pricing scraper."""
    providers: Optional[List[str]] = Field(
        default=None,
        description="Optional list of provider keys to scrape (e.g., ['openai', 'groq']). If null, scrapes all."
    )


class PricingScraperResponse(BaseModel):
    """Response after running the pricing scraper."""
    status: str
    message: str


# ============================================================================
# Sync Models Schemas
# ============================================================================

class SyncModelsResponse(BaseModel):
    """Response after syncing models from provider APIs."""
    success: bool
    message: str
    providers_synced: Optional[int] = None
    models_discovered: Optional[int] = None
    models_activated: Optional[int] = None
    errors: Optional[List[str]] = None


# ============================================================================
# Health Check
# ============================================================================

class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: str
    service: str
    version: str


# ============================================================================
# Error Response
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    message: str
    details: Optional[str] = None
