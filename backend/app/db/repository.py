import sqlite3
import time
from typing import Any, Dict, List, Tuple, Generator
from contextlib import contextmanager

from app.db.session import get_db, get_db_ctx
from app.core.config import (
    USE_MOCK_DB,
    DB_PATH,
    MOCK_DB_PATH,
    DB_RECORD_EXPIRY_SECONDS
)
from app.core.logger import logger

# ─── Initialization

def init_db():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icao24 TEXT UNIQUE,
        timestamp INTEGER DEFAULT (strftime('%s', 'now')),
        callsign TEXT,
        origin_country TEXT,
        time_position INTEGER,
        last_contact INTEGER,
        longitude REAL,
        latitude REAL,
        baro_altitude REAL,
        on_ground INTEGER,
        velocity REAL,
        true_track REAL,
        vertical_rate REAL,
        geo_altitude REAL,
        squawk TEXT,
        position_source INTEGER,
        category INTEGER
    );
    """
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_flight_timestamp   ON states(timestamp);
    CREATE INDEX IF NOT EXISTS idx_flight_icao24      ON states(icao24);
    CREATE INDEX IF NOT EXISTS idx_flight_coordinates ON states(latitude, longitude);
    """

    with get_db_ctx() as conn:
        conn.executescript(create_table_sql + create_index_sql)
        conn.commit()

# ─── Upsert Logic

def upsert_states(
    conn: sqlite3.Connection,
    states: List[List[Any]]
) -> Tuple[int,int]:
    total = len(states)
    cursor = conn.cursor()
    for state in states:
        values = tuple(state[:12] + state[13:15] + state[16:18])
        cursor.execute("""
            INSERT INTO states (
                icao24, callsign, origin_country, time_position, last_contact, longitude, latitude, baro_altitude, on_ground, velocity, true_track, vertical_rate, geo_altitude, squawk, position_source, category
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(icao24) DO UPDATE SET
                timestamp = (strftime('%s', 'now')),
                callsign = excluded.callsign,
                origin_country = excluded.origin_country,
                time_position = excluded.time_position,
                last_contact = excluded.last_contact,
                longitude = excluded.longitude,
                latitude = excluded.latitude,
                baro_altitude = excluded.baro_altitude,
                on_ground = excluded.on_ground,
                velocity = excluded.velocity,
                true_track = excluded.true_track,
                vertical_rate = excluded.vertical_rate,
                geo_altitude = excluded.geo_altitude,
                squawk = excluded.squawk,
                position_source = excluded.position_source,
                category = excluded.category
            """, values)
    conn.commit()
    affected = cursor.rowcount
    return total, affected

# ─── Cleanup Expired Records

def remove_expired_states(conn: sqlite3.Connection) -> int:
    threshold = int(time.time()) - DB_RECORD_EXPIRY_SECONDS
    cursor = conn.execute(
        "DELETE FROM states WHERE timestamp < ?",
        (threshold,)
    )
    conn.commit()
    return cursor.rowcount

# ─── Query with Filters, Pagination, Sorting

def query_states(
    conn: sqlite3.Connection,
    filters: Dict[str, Any],
    page_size: int = 50,
    cursor: int = None,
    sort_field: str = None,
    sort_order: str = None
) -> Dict[str, Any]:
    sort_field = sort_field or "id"
    sort_order = (sort_order or "ASC").upper()

    where_clauses = ["latitude IS NOT NULL AND longitude IS NOT NULL"]
    params: List[Any] = []

    for key, raw in filters.items():
        if raw is None:
            continue
        values = raw if isinstance(raw, list) else [raw]

        if len(values) > 1:
            placeholders = ",".join("?" * len(values))
            where_clauses.append(f"{key} IN ({placeholders})")
            params.extend(values)
        else:
            value = values[0]
            if key.endswith("_gt") or key.endswith("_lt"):
                op = ">" if key.endswith("_gt") else "<"
                column = key.rsplit("_", 1)[0]
                where_clauses.append(f"{column} {op} ?")
                params.append(value)
            else:
                where_clauses.append(f"{key} LIKE ?")
                params.append(f"%{value}%")

    # Cursor pagination
    if cursor is not None:
        where_clauses.append("id > ?")
        params.append(cursor)

    where_sql = " AND ".join(where_clauses)
    count_sql = f"SELECT COUNT(*) FROM states WHERE {where_sql}"
    data_sql = (
        f"SELECT * FROM states "
        f"WHERE {where_sql} "
        f"ORDER BY {sort_field} {sort_order.upper()} "
        f"LIMIT ?"
    )
    params_with_limit = params + [page_size]

    # Total count
    total = conn.execute(count_sql, params).fetchone()[0]
    # Page of results
    rows = conn.execute(data_sql, params_with_limit).fetchall()
    results = [dict(r) for r in rows]
    next_cursor = results[-1]["id"] if results else None

    return {
        "results_count": total,
        "page_size": page_size,
        "next_cursor": next_cursor,
        "results": results
    }