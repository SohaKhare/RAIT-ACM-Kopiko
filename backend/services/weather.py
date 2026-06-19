import httpx
from datetime import date, datetime


OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"


async def get_rainfall_data(lat: float, lon: float) -> dict:
    """
    Single API call: 30 past days + 7 future days = 37 entries.
    Split at today's date into historical vs forecast.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(OPEN_METEO_FORECAST, params={
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum",
            "timezone": "Asia/Kolkata",
            "past_days": 30,
            "forecast_days": 7
        })
        resp.raise_for_status()
        data = resp.json()

    times = data["daily"]["time"]
    precip = data["daily"]["precipitation_sum"]
    today_str = date.today().isoformat()

    past = []
    forecast = []
    for t, p in zip(times, precip):
        entry = {"date": t, "precipitation_mm": p}
        if t < today_str:
            past.append(entry)
        else:
            forecast.append(entry)

    past_total = sum(e["precipitation_mm"] or 0 for e in past)
    forecast_total = sum(e["precipitation_mm"] or 0 for e in forecast)

    return {
        "past_30_days": past,
        "past_30_total_mm": round(past_total, 1),
        "forecast_7_days": forecast,
        "forecast_7_total_mm": round(forecast_total, 1),
    }
