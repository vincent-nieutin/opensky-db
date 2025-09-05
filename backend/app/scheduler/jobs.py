from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.flight_service import fetch_and_store_flights, cleanup_flights
from datetime import datetime
import os
from app.core.config import SCHEDULER_FETCH_INTERVAL_SECONDS, SCHEDULER_CLEANUP_INTERVAL_MINUTES
from app.core.logger import logger

scheduler = BackgroundScheduler()

def start_scheduler():
    fetch_interval = int(SCHEDULER_FETCH_INTERVAL_SECONDS)
    logger.info(f"Starting fetch_and_store_flights scheduler with interval {fetch_interval} seconds")
    scheduler.add_job(
        fetch_and_store_flights,
        trigger=CronTrigger(second=f"*/{fetch_interval}")
    )

    cleanup_interval = int(SCHEDULER_CLEANUP_INTERVAL_MINUTES)
    logger.info(f"Starting cleanup_flights scheduler with interval {cleanup_interval} minutes")
    scheduler.add_job(
        cleanup_flights,
        trigger=CronTrigger(minute=f"*/{cleanup_interval}")
    )

    scheduler.start()

def stop_scheduler():
    scheduler.shutdown(wait=False)