import requests
import re
from supabase import create_client
from config import settings

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def _clean_location_string(loc: str) -> str:
    if not loc:
        return ""
    # Remove common suffixes that break DB matching (e.g., "Tawang district" -> "Tawang", "Bengaluru Urban" -> "Bengaluru")
    loc = re.sub(r'(?i)\b(district|urban|rural|nagar|city|town)\b', '', loc)
    return loc.strip()


def reverse_geocode(lat: float, lng: float):
    """
    Reverse geocode lat/lng to city, district, state using Nominatim (OpenStreetMap).
    Free, no API key needed. Rate limit: 1 req/sec.
    """
    resp = requests.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={
            "lat": lat, 
            "lon": lng, 
            "format": "json", 
            "addressdetails": 1,
            "accept-language": "en"  # Force English to avoid regional scripts (Urdu, Hindi, etc.)
        },
        headers={"User-Agent": "Kopiko/1.0 (agricultural-advisory)"},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    address = data.get("address", {})

    # Nominatim handles UTs (like Delhi) differently, often omitting 'state' or 'state_district'.
    # We fallback to other available geographic identifiers.
    city = address.get("city") or address.get("town") or address.get("village") or address.get("suburb", "")
    
    # District fallback: state_district -> county -> city district
    district = address.get("state_district") or address.get("county") or address.get("city_district", "")
    
    # State fallback: state -> state_code -> ISO3166-2-lvl4 -> city
    state = address.get("state")
    if not state:
        iso_state = address.get("ISO3166-2-lvl4", "")
        if iso_state.startswith("IN-"):
            # e.g., "IN-DL" -> "Delhi" mapping or just use city name for UTs
            state_codes = {"IN-DL": "Delhi", "IN-CH": "Chandigarh"}
            state = state_codes.get(iso_state, city)
        else:
            state = address.get("state_code", city)

    return {
        "city": _clean_location_string(city),
        "district": _clean_location_string(district),
        "state": _clean_location_string(state),
    }



def mandis_by_district(district, state):
    """
    Fetches all mandis in a given district within a state.
    """
    # 1. Find the district ID by name
    district_query = supabase.table("districts").select("id, district_name").ilike("district_name", f"%{district}%").limit(1).execute()
    
    if not district_query.data:
        return []
        
    district_id = district_query.data[0]["id"]
    
    # 2. Fetch all markets (mandis) for this district
    markets_query = supabase.table("markets").select("id, mkt_name").eq("district_id", district_id).execute()
    
    return [market["mkt_name"] for market in markets_query.data] if markets_query.data else []


def fetch_all_states_from_db():
    """
    Fetches all states ordered by state_name.
    """
    resp = supabase.table("states").select("state_id, state_name").order("state_name").execute()
    return [state["state_name"] for state in resp.data] if resp.data else []


def fetch_districts_by_state_from_db(state_name: str):
    """
    Fetches all districts in a given state name.
    """
    # Clean and match state name
    state_query = supabase.table("states").select("state_id").ilike("state_name", f"%{state_name.strip()}%").limit(1).execute()
    if not state_query.data:
        return []
    state_id = state_query.data[0]["state_id"]
    
    resp = supabase.table("districts").select("district_name").eq("state_id", state_id).order("district_name").execute()
    return [dist["district_name"] for dist in resp.data] if resp.data else []