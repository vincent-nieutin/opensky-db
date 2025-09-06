from fastapi import APIRouter, Request, Query
from fastapi.responses import FileResponse
from app.db.repository import query_flights

router = APIRouter(tags=["flights"])

@router.get("/")
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

@router.get("/emergencies")
def get_emergency_flights():
    return query_flights({"squawk": ["7500", "7600", "7700"]})

@router.get("/parameters")
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

@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         await websocket.send_json(get_latest_data())
#         await asyncio.sleep(10)