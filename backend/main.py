from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.routes.flights import router as flights_router
from app.db.repository import init_db, query_flights
from fastapi import APIRouter, Request, Query, WebSocket, WebSocketDisconnect
import json, asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    start_scheduler()

    yield

    # Shutdown logic
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

    filters = {}
    page_size = 50
    cursor = None
    
    try:
        while True:
            try:
                # Wait for new message for up to 10 seconds
                message = await asyncio.wait_for(websocket.receive_text(), timeout=10)
                params = json.loads(message)
                filters = params.get("filters", {})
                page_size = params.get("page_size", 50)
                cursor = params.get("cursor", None)
                print("Received params:", params)

                data = query_flights(filters, page_size=page_size, cursor=cursor)
                await websocket.send_json(data)
            except asyncio.TimeoutError:
                # No new message, continue with previous params
                pass
    except WebSocketDisconnect:
        print("WebSocket disconnected")