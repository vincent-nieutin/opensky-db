from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.routes.flights import router as flights_router
from app.db.repository import init_db

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