from pydantic import BaseModel
from typing import Optional


class MandiRequest(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    market: Optional[str] = None
