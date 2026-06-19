from fastapi import APIRouter
from models.mandi import MandiRequest
from controllers.mandi import fetch_mandi_data

router = APIRouter(prefix="/mandi", tags=["Mandi"])

@router.post("")
async def get_mandi(request: MandiRequest):
    """
    Fetch mandi price/arrival data for given state/district/market.
    """
    return fetch_mandi_data(request.state, request.district, request.market)
