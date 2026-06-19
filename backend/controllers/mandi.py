from typing import Optional
from services.mandi import get_mandi_data

def fetch_mandi_data(state: Optional[str], district: Optional[str], market: Optional[str]):
    return get_mandi_data(state=state, district=district, market=market)
