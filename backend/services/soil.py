import httpx


ISRIC_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def get_soil_data(lat: float, lon: float) -> dict:
    """
    Fetches soil data from two sources:
    1. ISRIC SoilGrids   -> pH, Nitrogen, Organic Carbon, Clay/Sand/Silt
    2. Open-Meteo         -> Soil Temperature & Soil Moisture (real-time)
    """
    chemistry = await _fetch_isric(lat, lon)
    moisture = await _fetch_open_meteo_soil(lat, lon)

    return {
        "chemistry": chemistry,
        "moisture_and_temperature": moisture
    }


async def _fetch_isric(lat: float, lon: float) -> dict:
    """
    ISRIC SoilGrids API for soil chemistry at 0-5cm depth.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "property": ["phh2o", "soc", "nitrogen", "clay", "sand", "silt"],
        "depth": "0-5cm"
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(ISRIC_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        # Parse the layers into a clean dict
        result = {}
        for layer in data.get("properties", {}).get("layers", []):
            name = layer["name"]
            d_factor = layer.get("unit_measure", {}).get("d_factor", 1)
            target_units = layer.get("unit_measure", {}).get("target_units", "")
            depths = layer.get("depths", [])
            if depths:
                mean_val = depths[0].get("values", {}).get("mean")
                result[name] = {
                    "value": round(mean_val / d_factor, 2) if mean_val is not None else None,
                    "unit": target_units
                }
        return result
    except Exception as e:
        print(f"ISRIC SoilGrids fetch failed: {e}")
        return {}


async def _fetch_open_meteo_soil(lat: float, lon: float) -> dict:
    """
    Open-Meteo API for real-time soil moisture and soil temperature.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "soil_temperature_0cm,soil_moisture_0_to_1cm",
        "timezone": "Asia/Kolkata",
        "forecast_days": 1
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        hourly = data.get("hourly", {})
        temps = hourly.get("soil_temperature_0cm", [])
        moisture = hourly.get("soil_moisture_0_to_1cm", [])

        # Return the latest non-null reading
        latest_temp = next((t for t in reversed(temps) if t is not None), None)
        latest_moisture = next((m for m in reversed(moisture) if m is not None), None)

        return {
            "soil_temperature_c": latest_temp,
            "soil_moisture_m3_per_m3": latest_moisture
        }
    except Exception as e:
        print(f"Open-Meteo soil fetch failed: {e}")
        return {}
