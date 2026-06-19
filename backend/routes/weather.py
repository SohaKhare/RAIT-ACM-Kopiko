from fastapi import APIRouter
from models.weather import WeatherRequest
from controllers.weather import fetch_weather

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.post("")
async def get_weather(request: WeatherRequest):
    """
    Get 37 days of rainfall data (30 past + 7 forecast) in a single API call.
    """
    return await fetch_weather(request.lat, request.lng)
