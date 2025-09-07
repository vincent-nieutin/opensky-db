import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# OpenSky API credentials
OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")
OPENSKY_TOKEN_URL = os.getenv("OPENSKY_TOKEN_URL")
OPENSKY_TOKEN_EXPIRY_SECONDS = os.getenv("OPENSKY_TOKEN_EXPIRY_SECONDS", 1800)
OPENSKY_API_URL = os.getenv("OPENSKY_API_URL")

# Database
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "False") in ("True")
DB_PATH = os.getenv("DB_PATH", "db/flight_data.db")
MOCK_DB_PATH = os.getenv("MOCK_DB_PATH", "db/mock_flight_data.db")
DB_RECORD_EXPIRY_SECONDS = os.getenv("DB_RECORD_EXPIRY_SECONDS", 10)

# Scheduler
SCHEDULER_FETCH_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_FETCH_INTERVAL_SECONDS", 25))
SCHEDULER_CLEANUP_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_CLEANUP_INTERVAL_MINUTES", 10))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
