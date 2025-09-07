import json
import asyncio
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.db.repository import init_db, query_flights
from app.core.logger import logger
from app.core.config import USE_MOCK_DB, SCHEDULER_FETCH_INTERVAL_SECONDS, CORS_ORIGINS

# ─── Constants

DEFAULT_PAGE_SIZE = 50
DEFAULT_FILTERS = {}
DEFAULT_SORT = {"field": None, "order": None}

# ─── Lifespan (startup / shutdown)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not USE_MOCK_DB:
        start_scheduler()
    yield
    if not USE_MOCK_DB:
        stop_scheduler()

# ─── App & Middleware

app = FastAPI(title="OpenSky DB API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Helper: query & send

async def _send_flights(
    ws: WebSocket,
    filters: Dict[str, Any],
    page_size: int,
    cursor: Any,
    sort_field: Any,
    sort_order: Any
):
    try:
        payload = query_flights(
            filters=filters,
            page_size=page_size,
            cursor=cursor,
            sort_field=sort_field,
            sort_order=sort_order
        )
        await ws.send_json(payload)
    except Exception as e:
        logger.error("Failed to query/send flights: %s", e)
        # Optionally notify client of error
        await ws.send_json({"error": "internal_server_error"})

# ─── WebSocket Endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client = f"{websocket.client.host}:{websocket.client.port}"
    logger.info("WebSocket connected: %s", client)
    
    filters = DEFAULT_FILTERS.copy()
    page_size = DEFAULT_PAGE_SIZE
    cursor = None
    sort = DEFAULT_SORT
    
    try:
        while True:
            try:
                # wait for incoming params or timeout
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=SCHEDULER_FETCH_INTERVAL_SECONDS
                )
                params = json.loads(message)
                filters = params.get("filters", filters)
                page_size = params.get("page_size", page_size)
                cursor = params.get("cursor", cursor)
                sort = {
                    "field": params.get("sort_field", sort["field"]),
                    "order": params.get("sort_order", sort["order"]),
                }

            except asyncio.TimeoutError:
                pass

            await _send_flights(
                websocket,
                filters,
                page_size,
                cursor,
                sort["field"],
                sort["order"],
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", client)
    except Exception as e:
        logger.exception("WebSocket %s encountered error: %s", client, e)
        await websocket.close(code=1011)

# ─── Favicon Endpoint

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")