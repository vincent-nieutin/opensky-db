from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import WebSocket, WebSocketDisconnect
import json, asyncio

from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.routes.flights import router as flights_router
from app.db.repository import init_db, query_flights
from app.core.logger import logger
from app.core.config import USE_MOCK_DB, SCHEDULER_FETCH_INTERVAL_SECONDS

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()

    if not USE_MOCK_DB:
        start_scheduler()

    yield

    # Shutdown logic
    if not USE_MOCK_DB:
        stop_scheduler()

app = FastAPI(lifespan=lifespan, title="OpenSky DB API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(flights_router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket {websocket.client.host}:{websocket.client.port} connected")
    
    filters = {}
    page_size = 50
    cursor = None
    sort_field = None
    sort_order = None
    
    try:
        while True:
            try:
                # Wait for new message for up to 10 seconds
                message = await asyncio.wait_for(websocket.receive_text(), timeout=SCHEDULER_FETCH_INTERVAL_SECONDS)
                params = json.loads(message)
                filters = params.get("filters", {})
                page_size = params.get("page_size", 50)
                cursor = params.get("cursor", None)
                sort_field = params.get("sort_field", None)
                sort_order = params.get("sort_order", None)

                data = query_flights(filters, page_size=page_size, cursor=cursor, sort_field=sort_field, sort_order=sort_order)
                await websocket.send_json(data)
            except asyncio.TimeoutError:
                data = query_flights(filters, page_size=page_size, cursor=cursor, sort_field=sort_field, sort_order=sort_order)
                await websocket.send_json(data)

    except WebSocketDisconnect:
        logger.info(f"WebSocket {websocket.client.host}:{websocket.client.port} disconnected")