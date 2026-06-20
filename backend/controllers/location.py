from services.location import (
    reverse_geocode, 
    mandis_by_district, 
    fetch_all_states_from_db, 
    fetch_districts_by_state_from_db
)


def fetch_location(lat: float, lng: float):
    return reverse_geocode(lat, lng)

def fetch_mandis(district: str, state: str | None = None):
    return mandis_by_district(district, state)

def fetch_states():
    return fetch_all_states_from_db()

def fetch_districts(state: str):
    return fetch_districts_by_state_from_db(state)
