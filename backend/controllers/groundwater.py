from services.groundwater import get_groundwater_data

def fetch_groundwater_recent(state: str, place: str):
    return get_groundwater_data(state, place)
