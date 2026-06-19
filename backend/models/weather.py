from pydantic import BaseModel

class WeatherRequest(BaseModel):
    lat: float
    lng: float
