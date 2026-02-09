"""
Pricing Router

Endpoints for running the pricing scraper:
  - POST /api/pricing/scrape   → Trigger pricing scraper (background)
  - GET  /api/pricing/scrape   → Trigger pricing scraper (for cron compatibility)
"""

import traceback
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.schemas import PricingScraperRequest, PricingScraperResponse, ErrorResponse

from pricing_scraper.pricing_scraper import run_pricing_scraper

router = APIRouter(
    prefix="/api/pricing",
    tags=["Pricing"],
)


def _run_scraper_background(providers: Optional[List[str]] = None):
    """Background task wrapper for running the pricing scraper."""
    try:
        run_pricing_scraper(providers=providers)
    except Exception as e:
        print(f"❌ Background pricing scraper failed: {e}")
        traceback.print_exc()


@router.post(
    "/scrape",
    response_model=PricingScraperResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Run pricing scraper (background)",
    description=(
        "Scrape pricing data from all or specified providers. "
        "Runs in the background — returns immediately."
    ),
)
def pricing_scrape_post(
    body: PricingScraperRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger pricing scraper via POST with optional provider filter."""
    background_tasks.add_task(_run_scraper_background, providers=body.providers)

    return PricingScraperResponse(
        status="accepted",
        message="Pricing scraper started in background",
    )


@router.get(
    "/scrape",
    response_model=PricingScraperResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Run pricing scraper (synchronous, cron-friendly)",
    description=(
        "Synchronous GET endpoint for Vercel Cron. "
        "Scrapes pricing data and returns after completion."
    ),
)
def pricing_scrape_get(
    providers: Optional[str] = Query(
        default=None,
        description="Comma-separated provider keys (e.g., 'openai,groq'). If omitted, scrapes all.",
    ),
):
    """Run pricing scraper synchronously (for Vercel Cron)."""
    try:
        provider_list = [p.strip() for p in providers.split(",")] if providers else None
        run_pricing_scraper(providers=provider_list)
        return PricingScraperResponse(
            status="success",
            message="Pricing scraper completed successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
