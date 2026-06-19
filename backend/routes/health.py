from fastapi import APIRouter
from controllers.health import check_health

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    return check_health()
