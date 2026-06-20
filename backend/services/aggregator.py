import os
import json
from models.location import Location
from services.mandi import get_mandi_data
from services.weather import get_rainfall_data
from services.groundwater import get_groundwater_data
from models.groundwater import Groundwater, GroundwaterMLResponse
from services.groundwater_ml import predict_groundwater
from services.soil import get_soil_data

# Here we are aggregating all the data we gathered into a single pipeline.

async def _get_crop_water_requirement(depth: float):
    """
    Parses groundwater depth and sorts crops from crop_water_requirements.json
    based on their drought tolerance and water requirements.
    """
    # 2. Determine Water Status
    if depth > 30.0:
        gw_status = "critical"      # Water table is severely depleted
    elif depth > 10.0:
        gw_status = "moderate"      # Water table is okay, but requires caution
    else:
        gw_status = "safe"          # Water is abundant (e.g. 9.095m)

    # 3. Load Crop JSON Data
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "crop_water_requirements.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            crops = json.load(f)["crop_water_requirements"]
    except Exception as e:
        print(f"Failed to load crop data: {e}")
        return []

    # 4. Score and Sort Crops based on Groundwater
    for crop in crops:
        score = 100.0  # Base Score
        
        # Adjust scores based on water availability
        if gw_status == "critical":
            # Boost drought-resistant crops
            if crop["drought_tolerance"] == "high" or crop["category"] in ["low_water", "very_low_water"]:
                score += 50.0  
            # Heavily penalize water-intensive crops (like Paddy)
            if crop["category"] == "high_water":
                score -= 60.0  
                
        elif gw_status == "moderate":
            # Mildly penalize high water crops
            if crop["category"] == "high_water":
                score -= 30.0  
                
        crop["recommendation_score"] = score

    # Sort crops so the highest recommended ones appear at the top
    crops.sort(key=lambda x: x["recommendation_score"], reverse=True)
    
    return {
        "groundwater_depth_m": depth,
        "groundwater_status": gw_status,
        "ranked_crops": crops
    }


async def _aggregate_locational_data(location: Location):
    district = location.district
    state = location.state
    mandi = location.mandi
    lat = location.lat
    lng = location.lng

    # 1. Gather all raw data
    mandi_data = get_mandi_data(state, district, mandi)
    # Get ML prediction
    groundwater_data = predict_groundwater(state=state, district=district)
    weather_data = await get_rainfall_data(lat, lng)
    soil_data = await get_soil_data(lat, lng)

    # 2. Process Groundwater Data & Get AI-Sorted Crop Recommendations
    depth = 0.0
    clean_groundwater = {}
    if groundwater_data:
        # Parse into ML Response model
        gw_ml = GroundwaterMLResponse(**groundwater_data)
        depth = gw_ml.current_depth
        clean_groundwater = gw_ml.model_dump()

    crop_recommendations = await _get_crop_water_requirement(depth)

    # 3. Clean up Mandi Data
    # Safely extract mandi records (APIs sometimes return lists instead of dicts when empty)
    clean_mandi = []
    api_resp = mandi_data.get("api_response", {})
    if isinstance(api_resp, dict):
        data_block = api_resp.get("data", {})
        if isinstance(data_block, dict):
            clean_mandi = data_block.get("records", [])

    # 4. Return the fully aggregated payload
    return {
        "location": {
            "state": state,
            "district": district,
            "mandi": mandi
        },
        "weather": weather_data,
        "groundwater": clean_groundwater,
        "mandi": clean_mandi,
        "soil": soil_data,
        "agriculture_advisory": crop_recommendations
    }
