from typing import Any, List
from app.db.session import get_db_ctx
from app.db.repository import upsert_states, remove_expired_states
from app.integrations.opensky import fetch_states
from app.core.logger import logger

from contextlib import ExitStack

def fetch_and_store_flights() -> None:
    """
    Fetch the latest flight states from OpenSky and upsert them into the DB.
    Logs inserted vs. updated counts, or warns if no data arrives.
    """
    states: List[List[Any]] = fetch_states()

    with get_db_ctx() as conn:
        inserted, updated = upsert_states(conn, states)
    logger.info("States upsert complete: %d inserted, %d updated", inserted, updated)

def cleanup_states() -> None:
    """
    Delete expired flight records from the DB.
    Logs how many rows were removed.
    """
    with get_db_ctx() as conn:
        removed = remove_expired_states(conn)
        logger.info("Expired states delete complete: %d removed", removed)
