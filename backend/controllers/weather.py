from services.weather import get_rainfall_data

async def fetch_weather(lat: float, lng: float):
    return await get_rainfall_data(lat, lng)
