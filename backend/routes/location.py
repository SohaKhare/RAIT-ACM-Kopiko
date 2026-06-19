from fastapi import APIRouter
from models.location import LocationRequest
from controllers.location import fetch_location

router = APIRouter(prefix="/location", tags=["Location"])


@router.post("")
async def get_location(request: LocationRequest):
    """
    Reverse geocode lat/lng to city, district, state.
    """
    return fetch_location(request.lat, request.lng)
