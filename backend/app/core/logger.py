import os
import sys
import logging
from app.core.config import LOG_FILE, LOG_LEVEL, ENVIRONMENT

log_level = getattr(logging, LOG_LEVEL, logging.INFO)

# Create a logger
logger = logging.getLogger("app_logger")
logger.setLevel(log_level)  # Set the minimum log level

# Define a common formatter
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)
console_handler.setFormatter(formatter)

# File handler if on dev
if ENVIRONMENT == "development":
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

# Add both handlers to the logger if not already configured
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    if ENVIRONMENT == "development":
        logger.addHandler(file_handler)
