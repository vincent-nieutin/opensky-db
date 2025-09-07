import time
from typing import List, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import (
    OPENSKY_CLIENT_ID,
    OPENSKY_CLIENT_SECRET,
    OPENSKY_TOKEN_URL,
    OPENSKY_TOKEN_EXPIRY_SECONDS,
    OPENSKY_API_URL
)
from app.core.logger import logger

# ─── Module-Level Session with Retries

_session = requests.Session()
_retry_strategy = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["POST", "GET"],
)
_adapter = HTTPAdapter(max_retries=_retry_strategy)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

# ─── Token Cache

_token_cache = {
    "access_token": None,
    "expires_at": 0  # Unix timestamp
}

def _is_token_valid() -> bool:
    return (
        _token_cache["access_token"] is not None
        and time.time() < _token_cache["expires_at"] - 60
    )

def get_opensky_token() -> str:
    now = time.time()

    if _is_token_valid():
        return _token_cache["access_token"]

    payload = {
        "client_id": OPENSKY_CLIENT_ID,
        "client_secret": OPENSKY_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    logger.debug("Requesting new OpenSky token")
    response = _session.post(OPENSKY_TOKEN_URL, data=payload, timeout=10)
    response.raise_for_status()

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("No access_token in OpenSky response")

    expires_in = data.get("expires_in", OPENSKY_TOKEN_EXPIRY_SECONDS)
    _token_cache.update({
        "access_token": token,
        "expires_at": time.time() + float(expires_in),
    })

    logger.info("Obtained new OpenSky token, expires in %s seconds", expires_in)
    return token


def fetch_flight_data() -> List[Any]:
    token = get_opensky_token()
    headers = { "Authorization": f"Bearer {token}" }

    logger.info("Fetching flight data from Opensky API")
    response = _session.get(OPENSKY_API_URL, headers=headers, timeout=10)
    response.raise_for_status()

    payload = response.json()
    states = payload.get("states", [])
    logger.info("Fetched %d flight states", len(states))
    return states