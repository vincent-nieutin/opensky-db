import sqlite3, time, os
from app.core.config import DB_PATH, DB_RECORD_EXPIRY_SECONDS
from app.core.logger import logger

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flight_data (
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
    )
    """)
    conn.commit()
    conn.close()

def upsert_flight_data(states):
    conn = get_db()
    cursor = conn.cursor()

    inserted = 0
    updated = 0

    for state in states:
        values = tuple(state[:12] + state[13:15] + state[16:18])

        # Check if the record already exists
        cursor.execute("SELECT 1 FROM flight_data WHERE icao24 = ?", (values[0],))
        exists = cursor.fetchone()

        cursor.execute("""
            INSERT INTO flight_data (
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
    
        if exists:
            updated += 1
        else:
            inserted += 1

    conn.commit()
    conn.close()

    return inserted, updated

def remove_expired_flights():
    logger.info("Cleaning up expired flight data")
    conn = get_db()
    cursor = conn.cursor()
    threshold = int(time.time()) - int(DB_RECORD_EXPIRY_SECONDS)
    cursor.execute("DELETE FROM flight_data WHERE timestamp < ?", (threshold,))
    conn.commit()
    conn.close()
    logger.info(f"Successfully removed {cursor.rowcount} records")

def get_latest_fetch_time():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(timestamp) FROM flight_data")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def query_flights(filters: dict, page_size: int = 50, cursor: int = None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor_obj = conn.cursor()

    base_query = "SELECT * FROM flight_data"
    count_query = "SELECT COUNT(*) FROM flight_data"
    conditions = []
    params = []
    count_params = []

    for key, values in filters.items():
        if not isinstance(values, list):
            values = [values]

        if len(values) > 1:
            placeholders = ", ".join(["?"] * len(values))
            conditions.append(f"{key} IN ({placeholders})")
            params.extend(values)
            count_params.append(values[0])
        else:
            value = values[0]
            if key.endswith("_gt"):
                column = key[:-3]
                conditions.append(f"{column} > ?")
                params.append(value)
                count_params.append(value)
            elif key.endswith("_lt"):
                column = key[:-3]
                conditions.append(f"{column} < ?")
                params.append(value)
                count_params.append(value)
            else:
                conditions.append(f"{key} LIKE ?")
                params.append(f"%{value}%")
                count_params.append(f"%{value}%")

    # Cursor condition
    if cursor is not None:
        conditions.append("id > ?")
        params.append(cursor)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
        count_query += " WHERE " + " AND ".join(conditions[:-1] if cursor else conditions)

    base_query += " ORDER BY id ASC LIMIT ?"
    params.append(page_size)

    # Execute count query
    cursor_obj.execute(count_query, count_params)
    results_count = cursor_obj.fetchone()[0]
    
    # Execute data query
    cursor_obj.execute(base_query, params)
    results = [dict(row) for row in cursor_obj.fetchall()]
    conn.close()

    next_cursor = results[-1]['id'] if results else None

    return {
        "results_count": results_count,
        "page_size": page_size,
        "next_cursor": next_cursor,
        "results": results
        }