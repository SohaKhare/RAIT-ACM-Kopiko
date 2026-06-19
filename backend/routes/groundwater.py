from fastapi import APIRouter
from pydantic import BaseModel
from controllers.groundwater import fetch_groundwater_recent

router = APIRouter(prefix="/groundwater", tags=["Ground Water"])

class GroundWaterRequest(BaseModel):
    state: str
    place: str

@router.post("")
async def get_groundwater(request: GroundWaterRequest):
    """
    Fetch groundwater data for a specific state and taluka/village.
    """
    return fetch_groundwater_recent(request.state, request.place)
