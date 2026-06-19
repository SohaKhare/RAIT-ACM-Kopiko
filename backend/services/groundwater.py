import requests
import csv
import os
from datetime import datetime
import urllib3

# Suppress InsecureRequestWarning for gov sites with SSL issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "CGWB_dataset_CLEANED.csv")

def get_groundwater_data(state: str, place: str):
    # Mapping state/place to district if possible using CSV
    search_place = place.strip().lower()
    target_state = state.strip()
    district = target_state # Fallback to state name if district not found (rarely useful for API but keeps a value)
    found_district = False
    
    # Try to find the district from CSV if place is a tehsil or village
    try:
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Match state first to be accurate
                    if row['State'].strip().lower() == target_state.lower():
                        # Check if 'place' matches Village, Tehsil, or even District in the CSV
                        row_village = row.get('Village', '').strip().lower()
                        row_tehsil = row.get('Tehsil', '').strip().lower()
                        row_district = row.get('District', '').strip().lower()

                        if search_place in [row_village, row_tehsil, row_district]:
                            district = row['District'].strip()
                            found_district = True
                            break
                
                # If still not found, just use the 'place' as the district name for the API call
                if not found_district:
                    district = place.strip()

    except Exception as e:
        print(f"Error reading CSV for district mapping: {e}")
        district = place.strip()

    # API Configuration
    # IndiaWRIS often expects exact names.
    url = "https://indiawris.gov.in/Dataset/Ground%20Water%20Level"
    params = {
        "stateName": target_state,
        "districtName": district,
        "agencyName": "CGWB",
        "startdate": "2026-05-01",
        "enddate": "2026-06-25",
        "download": "false",
        "page": 0,
        "size": 10 # Changed from 1 to 10 to match example
    }
    
    try:
        # IndiaWRIS API often requires a POST request with params
        # verify=False is used to bypass SSL certificate issues often found in gov sites
        response = requests.post(url, params=params, timeout=15, verify=False)
        if response.status_code == 200:
            api_data = response.json()
            if api_data and "data" in api_data and api_data["data"]:
                # Sort by dataTime to ensure the most recent is first
                # The dataTime format is ISO-like: "2026-06-01T06:00:00"
                sorted_data = sorted(api_data["data"], key=lambda x: x.get("dataTime", ""), reverse=True)
                return {
                    "statusCode": 200,
                    "message": "Data fetched successfully from IndiaWRIS",
                    "data": [sorted_data[0]] if sorted_data else []
                }
    except Exception as e:
        print(f"API fetch failed: {e}")

    # Fallback to CSV
    try:
        fallback_data = []
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Match by state and (district or tehsil or village)
                    if row['State'].strip().lower() == target_state.lower() and \
                       (row['District'].strip().lower() == place.strip().lower() or \
                        row.get('Tehsil', '').strip().lower() == place.strip().lower() or \
                        row.get('Village', '').strip().lower() == place.strip().lower()):
                        
                        fallback_data.append({
                            "stationCode": "LOCAL_" + row.get("Station Name", "NA"),
                            "stationName": row.get("Station Name", "N/A"),
                            "stationType": "Ground Water",
                            "latitude": None,
                            "longitude": None,
                            "agencyName": "CGWB",
                            "state": row.get("State"),
                            "district": row.get("District"),
                            "majorBasin": None,
                            "tributary": None,
                            "dataAcquisitionMode": "Manual (CSV Fallback)",
                            "stationStatus": "Active",
                            "tehsil": row.get("Tehsil", "-"),
                            "datatypeCode": "GGZ",
                            "description": "Ground Water Level",
                            "dataValue": float(row.get("Latest Reading", 0)) if row.get("Latest Reading") else 0,
                            "dataTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                            "unit": "m",
                            "block": None,
                            "village": row.get("Village"),
                            "wellType": "Bore Well",
                            "wellDepth": float(row.get("Well Depth", 0)) if row.get("Well Depth") else 0,
                            "wellAquiferType": "Unknown"
                        })
        
        if fallback_data:
            # Most recent from CSV is just the latest reading available
            return {
                "statusCode": 200,
                "message": "Data fetched successfully from local storage",
                "data": [fallback_data[0]] if fallback_data else []
            }
            
    except Exception as e:
        print(f"Fallback failed: {e}")

    return {
        "statusCode": 404,
        "message": "No data found for the given location in either API or local storage",
        "data": []
    }
