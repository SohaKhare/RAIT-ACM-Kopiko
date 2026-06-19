from fastapi import APIRouter
from pydantic import BaseModel
from services.aggregator import _aggregate_locational_data
from models.location import Location



router = APIRouter(prefix="/aggregator", tags=["Aggregator"])

@router.post("")
async def aggregate_data(location: Location):
    """Aggregates data from all services based on location."""
    try:
        result = await _aggregate_locational_data(location)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


