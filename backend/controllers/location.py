from services.location import reverse_geocode, mandis_by_district


def fetch_location(lat: float, lng: float):
    return reverse_geocode(lat, lng)

def fetch_mandis(district: str, state: str | None = None):
    return mandis_by_district(district, state)
