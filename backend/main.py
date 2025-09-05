from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.db.repository import init_db, query_flights

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

@app.get("/")
def get_flights(
    request: Request,
    page_size: int = 50,
    cursor: int = Query(None)
):
    query_params = request.query_params

    filters = {
        key: query_params.getlist(key)
        for key in query_params
        if key not in {"page_size", "cursor"}
    }

    return query_flights(filters, page_size=page_size, cursor=cursor)

@app.get("/emergencies")
def get_emergency_flights():
    return query_flights({"squawk": ["7500", "7600", "7700"]})

@app.get("/parameters")
def get_available_parameters():
    return {
        "icao24": "Aircraft identifier",
        "callsign": "Flight callsign",
        "origin_country": "Country of origin",
        "time_position": "Time of position report",
        "last_contact": "Time of last contact",
        "longitude": "Longitude in degrees",
        "latitude": "Latitude in degrees",
        "baro_altitude": "Barometric altitude in meters",
        "on_ground": "Wether the aircraft is on the ground or not",
        "velocity": "Velocity over ground in m/s",
        "true_track": "True track in degrees",
        "vertical_rate": "Vertical rate in m/s",
        "geo_altitude": "Geometric altitude in meters",
        "squawk": "Transponder code",
        "position_source": "Source of position information",
        "category": "Category of the transponder"
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")