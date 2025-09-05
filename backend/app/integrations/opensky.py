from app.core.config import OPENSKY_CLIENT_ID, OPENSKY_CLIENT_SECRET, OPENSKY_TOKEN_URL, OPENSKY_TOKEN_EXPIRY_SECONDS
import os, time, requests
from app.core.logger import logger

# Globals to store token and expiry
_token_cache = {
    "access_token": None,
    "expires_at": 0  # Unix timestamp
}

def get_opensky_token():
    now = time.time()

    # Check if token is still valid (with 1-minute buffer)
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    # Fetch new token
    payload = {
        "client_id": OPENSKY_CLIENT_ID,
        "client_secret": OPENSKY_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    response = requests.post(OPENSKY_TOKEN_URL, data=payload)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", OPENSKY_TOKEN_EXPIRY_SECONDS)

        # Cache token and expiry time
        _token_cache["access_token"] = access_token
        _token_cache["expires_at"] = now + expires_in

        return access_token
    else:
        raise Exception(f"Token request failed: {response.status_code} {response.text}")


def fetch_flight_data():
    token = get_opensky_token()
    headers = { "Authorization": f"Bearer {token}" }
    url = "https://opensky-network.org/api/states/all?extended=1"

    logger.info("Fetching flight data from Opensky API")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        states = response.json().get("states", [])
        logger.info(f"Fetched {len(states)} states")
        return states
    else:
        raise Exception(f"Opensky data request failed: {response.status_code} {response.text}")