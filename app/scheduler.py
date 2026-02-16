"""
APScheduler-based Scheduler

Replaces vercel.json cron definitions with an in-process scheduler.
Jobs are configured to match the original Vercel cron schedule:

  - Benchmark init:    every 15 minutes (0,15,30,45 * * * *)
  - Benchmark process: every 1 minute   (* * * * *)
  - Pricing scraper:   daily at midnight (0 0 * * *)
  - Sync models:       weekly Sunday 2AM (0 2 * * 0)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

_scheduler: BackgroundScheduler | None = None


def _job_benchmark_init():
    """Scheduled job: Initialize a new benchmark queue."""
    try:
        from benchmarking.queue_benchmark_runner import init_benchmark_queue
        print("\n⏰ [CRON] Initializing benchmark queue...")
        run_id = init_benchmark_queue(run_name="scheduled-run", triggered_by="scheduler")
        if run_id:
            print(f"⏰ [CRON] Benchmark queue initialized: {run_id}")
        else:
            print("⏰ [CRON] Failed to initialize benchmark queue")
    except Exception as e:
        print(f"⏰ [CRON] Benchmark init error: {e}")


def _job_benchmark_process():
    """Scheduled job: Process a batch from the benchmark queue."""
    try:
        from benchmarking.queue_benchmark_runner import run_benchmark_batch
        result = run_benchmark_batch(batch_size=10)
        status = result.get("status", "unknown")
        processed = result.get("processed", 0)
        if processed > 0:
            print(f"⏰ [CRON] Benchmark batch: {status}, processed={processed}")
    except Exception as e:
        print(f"⏰ [CRON] Benchmark process error: {e}")


def _job_pricing_scraper():
    """Scheduled job: Run the pricing scraper for all providers."""
    try:
        from pricing_scraper.pricing_scraper import run_pricing_scraper
        print("\n⏰ [CRON] Running pricing scraper...")
        run_pricing_scraper()
        print("⏰ [CRON] Pricing scraper complete")
    except Exception as e:
        print(f"⏰ [CRON] Pricing scraper error: {e}")


def _job_sync_models():
    """Scheduled job: Sync models from provider APIs."""
    try:
        from utils.provider_service import sync_models_to_database
        print("\n⏰ [CRON] Syncing models...")
        result = sync_models_to_database()
        if result["success"]:
            print(f"⏰ [CRON] Sync complete: {result['models_discovered']} models discovered")
        else:
            print(f"⏰ [CRON] Sync errors: {result['errors']}")
    except Exception as e:
        print(f"⏰ [CRON] Model sync error: {e}")


def start_scheduler():
    """
    Start the background scheduler with all cron jobs.
    Called during application startup (lifespan).
    
    Set DISABLE_SCHEDULER=1 to skip scheduler startup (e.g., in tests or
    when running behind an external cron system).
    """
    import os
    if os.getenv("DISABLE_SCHEDULER", "").strip() in ("1", "true", "yes"):
        print("⏰ Scheduler disabled via DISABLE_SCHEDULER env var")
        return

    global _scheduler
    _scheduler = BackgroundScheduler()

    # Benchmark init — every 15 minutes
    _scheduler.add_job(
        _job_benchmark_init,
        CronTrigger(minute="0,15,30,45"),
        id="benchmark_init",
        name="Initialize benchmark queue",
        replace_existing=True,
    )

    # Benchmark process — every minute
    _scheduler.add_job(
        _job_benchmark_process,
        CronTrigger(minute="*"),
        id="benchmark_process",
        name="Process benchmark batch",
        replace_existing=True,
    )

    # Pricing scraper — daily at midnight UTC
    _scheduler.add_job(
        _job_pricing_scraper,
        CronTrigger(hour=0, minute=0),
        id="pricing_scraper",
        name="Run pricing scraper",
        replace_existing=True,
    )

    # Sync models — weekly, Sunday at 2 AM UTC
    _scheduler.add_job(
        _job_sync_models,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="sync_models",
        name="Sync models from APIs",
        replace_existing=True,
    )

    _scheduler.start()
    print("⏰ Scheduler started with 4 cron jobs")


def get_scheduler_status() -> dict:
    """
    Return the current status of all scheduled jobs.
    Used by the /api/scheduler/status endpoint.
    """
    if _scheduler is None:
        return {"running": False, "jobs": [], "message": "Scheduler not initialized"}

    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": _scheduler.running,
        "job_count": len(jobs),
        "jobs": jobs,
    }


def shutdown_scheduler():
    """
    Gracefully shut down the scheduler.
    Called during application shutdown (lifespan).
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("⏰ Scheduler stopped")
