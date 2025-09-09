from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.flight_service import fetch_and_store_flights, cleanup_states
from app.core.config import (
    SCHEDULER_FETCH_INTERVAL_SECONDS,
    SCHEDULER_CLEANUP_INTERVAL_MINUTES,
)
from app.core.logger import logger

# ─── Scheduler Factory ───────────────────────────────────────────────────────

def _build_scheduler() -> BackgroundScheduler:
    """
    Create and configure the BackgroundScheduler instance.
    Uses UTC, sets a misfire grace time, and defines two interval jobs.
    """
    sched = BackgroundScheduler(
        timezone="UTC",
        job_defaults={
            "misfire_grace_time": 30,   # seconds
            "coalesce": True,           # merge runs if they pile up
            "max_instances": 1,         # avoid overlapping runs
        },
    )

    # Fetch job
    fetch_interval = int(SCHEDULER_FETCH_INTERVAL_SECONDS)
    sched.add_job(
        fetch_and_store_flights,
        trigger=IntervalTrigger(seconds=fetch_interval),
        id="fetch_and_store_flights",
        name="Fetch & Store Flights",
        replace_existing=True,
    )
    logger.info(
        "Scheduled fetch_and_store_flights every %d seconds",
        fetch_interval,
    )

    # Cleanup job
    cleanup_interval = int(SCHEDULER_CLEANUP_INTERVAL_MINUTES)
    sched.add_job(
        cleanup_states,
        trigger=IntervalTrigger(minutes=cleanup_interval),
        id="cleanup_states",
        name="Cleanup Expired States",
        replace_existing=True,
    )
    logger.info(
        "Scheduled cleanup_states every %d minutes",
        cleanup_interval,
    )

    return sched


# ─── Public API ──────────────────────────────────────────────────────────────

_scheduler: BackgroundScheduler = None

def start_scheduler() -> None:
    """
    Initialize and start the scheduler once.
    Subsequent calls have no effect.
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.info("Scheduler is already running; start_scheduler() skipped.")
        return

    _scheduler = _build_scheduler()
    _scheduler.start()
    logger.info("BackgroundScheduler started.")


def stop_scheduler(wait: bool = False) -> None:
    """
    Shutdown the scheduler if it’s running.
    :param wait: block until jobs finish if True
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=wait)
        logger.info("BackgroundScheduler stopped.")
    else:
        logger.info("Scheduler was not running; stop_scheduler() skipped.")
