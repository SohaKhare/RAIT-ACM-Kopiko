from pydantic import BaseModel
from typing import Optional, List

class GroundwaterDataPoint(BaseModel):
    stationCode: Optional[str] = None
    stationName: Optional[str] = None
    stationType: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    agencyName: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    dataValue: Optional[float] = None
    dataTime: Optional[str] = None
    unit: Optional[str] = None
    wellDepth: Optional[float] = None
    wellAquiferType: Optional[str] = None

class Groundwater(BaseModel):
    statusCode: int
    message: str
    data: Optional[List[GroundwaterDataPoint]] = None

class GroundwaterMLResponse(BaseModel):
    station: str
    current_depth: float
    predicted_depth: float
    health_score: float
    risk: str