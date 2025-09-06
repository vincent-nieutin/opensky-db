from app.core.logger import logger

def fetch_and_store_flights():
    try:
        from app.integrations.opensky import fetch_flight_data
        flight_data = fetch_flight_data()
        if flight_data:
            from app.db.repository import upsert_flight_data
            inserted, updated = upsert_flight_data(flight_data)
            logger.info(f"Successfully inserted {inserted} new records, updated {updated} existing records")
        else:
            logger.warning("No flight data received")
    except Exception as e:
        logger.error(f"Failed to fetch or store flights: {e}")

def cleanup_flights():
    try:
        from app.db.repository import remove_expired_flights
        remove_expired_flights()
    except Exception as e:
        logger.error(f"Failed to clean up flights: {e}")

