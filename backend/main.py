import json
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sqlite3

from app.db.session import get_db
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.db.repository import (
    init_db,
    query_states
)
from app.core.logger import logger
from app.core.config import (
    USE_MOCK_DB,
    SCHEDULER_FETCH_INTERVAL_SECONDS,
    ALLOW_ORIGINS,
    ENVIRONMENT
)

# ─── Constants

DEFAULT_PAGE_SIZE = 50
DEFAULT_FILTERS: Dict[str, Any] = {}
DEFAULT_SORT_FIELD: Optional[str] = None
DEFAULT_SORT_ORDER: Optional[str] = None

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
    allow_origins=ALLOW_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Helper: query & send

async def _send_flights(
    ws: WebSocket,
    conn: sqlite3.Connection,
    filters: Dict[str, Any],
    page_size: int,
    cursor: Any,
    sort_field: Any,
    sort_order: Any
):
    try:
        payload = query_states(
            conn=conn,
            filters=filters,
            page_size=page_size,
            cursor=cursor,
            sort_field=sort_field,
            sort_order=sort_order
        )
        await ws.send_json(payload)
    except Exception as e:
        logger.error("Failed to query/send flights: %s", e)
        # Notify client of error
        await ws.send_json({"error": "internal_server_error"})

# ─── WebSocket Endpoint

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    conn: sqlite3.Connection = Depends(get_db),
):
    await websocket.accept()
    client = f"{websocket.client.host}:{websocket.client.port}"
    logger.info("WebSocket connected: %s", client)
    
    filters = DEFAULT_FILTERS.copy()
    page_size = DEFAULT_PAGE_SIZE
    cursor = None
    sort_field = DEFAULT_SORT_FIELD
    sort_order = DEFAULT_SORT_ORDER
    
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
                sort_field = params.get("sort_field", sort_field)
                sort_order = params.get("sort_order", sort_order)

            except asyncio.TimeoutError:
                pass

            await _send_flights(
                websocket,
                conn,
                filters,
                page_size,
                cursor,
                sort_field,
                sort_order
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", client)
    except Exception as e:
        logger.exception("WebSocket %s encountered error: %s", client, e)
        await websocket.close(code=1011)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ─── Static & SPA Configuration

if ENVIRONMENT == "production":
    project_root = Path(__file__).parent.resolve()
    frontend_build = project_root / "client" / "build"

    app.mount(
        "/static",
        StaticFiles(directory=frontend_build / "static"),
        name="static"
    )

    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path, scope):
            response = await super().get_response(path, scope)
            if response.status_code == 404:
                return await super().get_response("index.html", scope)
            return response

    app.mount(
        "/",
        SPAStaticFiles(directory=frontend_build, html=True),
        name="spa"
    )