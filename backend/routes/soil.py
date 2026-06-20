from fastapi import APIRouter
from pydantic import BaseModel
from controllers.soil import fetch_soil

router = APIRouter(prefix="/soil", tags=["Soil"])


class SoilRequest(BaseModel):
    lat: float
    lon: float


@router.post("")
async def get_soil(request: SoilRequest):
    """
    Fetch soil chemistry (ISRIC) + moisture/temperature (Open-Meteo).
    """
    return await fetch_soil(request.lat, request.lon)
