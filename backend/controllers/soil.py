from services.soil import get_soil_data


async def fetch_soil(lat: float, lon: float):
    return await get_soil_data(lat, lon)
