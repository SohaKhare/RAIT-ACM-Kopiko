from fastapi import APIRouter
from models.location import LocationRequest, MandiRequest
from controllers.location import fetch_location, fetch_mandis, fetch_states, fetch_districts

router = APIRouter(prefix="/location", tags=["Location"])


@router.post("")
async def get_location(request: LocationRequest):
    """
    Reverse geocode lat/lng to city, district, state.
    """
    return fetch_location(request.lat, request.lng)

@router.post("/mandis")
async def get_mandis(request: MandiRequest):
    """
    Fetch all mandis for a given district.
    """
    return {"mandis": fetch_mandis(request.district, request.state)}

@router.get("/states")
async def get_states():
    """
    Fetch all states.
    """
    return {"states": fetch_states()}

@router.get("/districts")
async def get_districts(state: str):
    """
    Fetch all districts for a given state.
    ```
    state: Maharashtra
    ```
    """
    return {"districts": fetch_districts(state)}