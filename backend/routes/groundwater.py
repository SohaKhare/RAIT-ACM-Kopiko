from fastapi import APIRouter
from pydantic import BaseModel
from controllers.groundwater import fetch_groundwater_recent
from services.groundwater_ml import predict_groundwater

router = APIRouter(prefix="/groundwater", tags=["Ground Water"])

class GroundWaterRequest(BaseModel):
    state: str
    place: str

class GroundWaterMLRequest(BaseModel):
    state: str
    district: str

@router.post("")
async def get_groundwater(request: GroundWaterRequest):
    """
    Fetch groundwater data for a specific state and taluka/village.
    """
    return fetch_groundwater_recent(request.state, request.place)


@router.post("/ml")
async def get_groundwater_ml(request: GroundWaterMLRequest):
    """
    Fetch groundwater data for a specific state and district using the ML prediction.
    """
    return predict_groundwater(request.state, request.district)
