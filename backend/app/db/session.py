import sqlite3
from typing import Generator

from app.core.config import USE_MOCK_DB, DB_PATH, MOCK_DB_PATH

def ensure_db_folder_exists(path: str) -> None:
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Yield a sqlite3.Connection and ensure it’s closed afterward.
    """
    path = MOCK_DB_PATH if USE_MOCK_DB else DB_PATH
    ensure_db_folder_exists(path)
    # allow connections from multiple threads if needed
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

from contextlib import contextmanager
@contextmanager
def get_db_ctx() -> Generator[sqlite3.Connection, None, None]:
    path = MOCK_DB_PATH if USE_MOCK_DB else DB_PATH
    ensure_db_folder_exists(path)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()