"""
Sync Models Router

Endpoints for syncing available models from provider APIs:
  - POST /api/sync/models   → Trigger model sync (background)
  - GET  /api/sync/models   → Trigger model sync (for cron compatibility)
"""

import traceback

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.schemas import SyncModelsResponse, ErrorResponse

from utils.provider_service import sync_models_to_database

router = APIRouter(
    prefix="/api/sync",
    tags=["Sync"],
)


def _sync_models_background():
    """Background task wrapper for syncing models."""
    try:
        print("=" * 80)
        print(" STARTING MODEL SYNC")
        print("=" * 80)
        result = sync_models_to_database()
        if result["success"]:
            print("\n✅ Sync completed successfully!")
        else:
            print("\n❌ Sync failed with errors:")
            for error in result.get("errors", []):
                print(f"  - {error}")
    except Exception as e:
        print(f"❌ Background model sync failed: {e}")
        traceback.print_exc()


@router.post(
    "/models",
    response_model=SyncModelsResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Sync models from provider APIs (background)",
    description=(
        "Fetch available models from all provider APIs, register them in the database, "
        "and mark active models. Runs in the background."
    ),
)
def sync_models_post(background_tasks: BackgroundTasks):
    """Trigger model sync as a background task."""
    background_tasks.add_task(_sync_models_background)

    return SyncModelsResponse(
        success=True,
        message="Model sync started in background",
    )


@router.get(
    "/models",
    response_model=SyncModelsResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Sync models (synchronous, cron-friendly)",
    description=(
        "Synchronous GET endpoint for Vercel Cron. "
        "Fetches models from provider APIs, syncs to database, and returns results."
    ),
)
def sync_models_get():
    """Run model sync synchronously (for Vercel Cron)."""
    try:
        result = sync_models_to_database()
        if result["success"]:
            return SyncModelsResponse(
                success=True,
                message="Models synced successfully",
                providers_synced=result["providers_synced"],
                models_discovered=result["models_discovered"],
                models_activated=result["models_activated"],
            )
        else:
            return SyncModelsResponse(
                success=False,
                message="Model sync completed with errors",
                providers_synced=result.get("providers_synced"),
                models_discovered=result.get("models_discovered"),
                models_activated=result.get("models_activated"),
                errors=result.get("errors"),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/models/now",
    response_model=SyncModelsResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Sync models immediately (synchronous)",
    description=(
        "Run model sync synchronously and return full results. "
        "Use this when you need to confirm the sync completed."
    ),
)
def sync_models_now():
    """Run model sync synchronously and return results."""
    try:
        result = sync_models_to_database()

        if result["success"]:
            return SyncModelsResponse(
                success=True,
                message="Models synced successfully",
                providers_synced=result["providers_synced"],
                models_discovered=result["models_discovered"],
                models_activated=result["models_activated"],
            )
        else:
            return SyncModelsResponse(
                success=False,
                message="Model sync completed with errors",
                providers_synced=result.get("providers_synced"),
                models_discovered=result.get("models_discovered"),
                models_activated=result.get("models_activated"),
                errors=result.get("errors"),
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
