from services.location import reverse_geocode


def fetch_location(lat: float, lng: float):
    return reverse_geocode(lat, lng)
