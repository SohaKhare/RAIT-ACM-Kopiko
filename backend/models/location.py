from pydantic import BaseModel


class LocationRequest(BaseModel):
    lat: float
    lng: float


class Location(BaseModel):
    state: str | None = None
    district: str | None = None
    mandi: str | None = None
    lat: float
    lng: float

class MandiRequest(BaseModel):
    district: str
    state: str | None = None