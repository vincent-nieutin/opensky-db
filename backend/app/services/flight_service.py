from typing import Any, List

from app.integrations.opensky import fetch_flight_data
from app.db.repository import upsert_flight_data, remove_expired_flights
from app.core.logger import logger

def fetch_and_store_flights() -> None:
    """
    Fetch the latest flight states from OpenSky and upsert them into the DB.
    Logs inserted vs. updated counts, or warns if no data arrives.
    """
    try:
        states: List[Any] = fetch_flight_data()
        if not states:
            logger.warning("No flight data received from OpenSky")
            return

        inserted, updated = upsert_flight_data(states)
        logger.info(
            "Flight data upsert complete: %d inserted, %d updated",
            inserted,
            updated
        )
    except Exception:
        logger.exception("Failed to fetch and store flight data")


def cleanup_flights() -> None:
    """
    Delete expired flight records from the DB.
    Logs how many rows were removed.
    """
    try:
        deleted = remove_expired_flights()
        logger.info("Expired flight cleanup complete: %d records removed", deleted)
    except Exception:
        logger.exception("Failed to clean up expired flight records")
