import logging
from app.core.config import LOG_FILE, LOG_LEVEL

log_level = getattr(logging, LOG_LEVEL, logging.INFO)

# Create a logger
logger = logging.getLogger("app_logger")
logger.setLevel(log_level)  # Set the minimum log level

# Define a common formatter
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(log_level)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(formatter)

# Add both handlers to the logger if not already configured
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
