import os
import pickle
from datetime import datetime

import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "groundwater_model.pkl"
)

ENCODER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "encoders.pkl"
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "groundwater_history.csv"
)


with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(ENCODER_PATH, "rb") as f:
    encoders = pickle.load(f)

history_df = pd.read_csv(DATA_PATH)

history_df["Date"] = pd.to_datetime(
    history_df["Date"]
)

def calculate_health_score(
    current_depth: float,
    predicted_depth: float
):

    forecast_change = (
        predicted_depth -
        current_depth
    )

    depth_component = (
        1 -
        current_depth / 54.7
    ) * 100

    forecast_component = (
        1 -
        max(0, forecast_change) / 15
    ) * 100

    score = (
        0.7 * depth_component +
        0.3 * forecast_component
    )

    return round(
        max(0, min(100, score)),
        1
    )

def get_villages(state: str, district: str):
    data = history_df[
        (history_df["State"].str.lower() == state.lower())
        &
        (history_df["District"].str.lower() == district.lower())
    ]
    if data.empty:
        return []
    
    # Using 'Station Name' as 'Village'
    villages = sorted(data["Station Name"].unique().tolist())
    return villages

def get_risk(score):

    if score >= 80:
        return "Safe"

    elif score >= 60:
        return "Moderate"

    elif score >= 40:
        return "High Risk"

    return "Critical"

def predict_groundwater(
    state: str,
    district: str,
    village: str | None = None
):
    # Filter by state and district first
    base_data = history_df[
        (history_df["State"].str.lower() == state.lower())
        &
        (history_df["District"].str.lower() == district.lower())
    ]

    if base_data.empty:
        return None

    # Determine which stations to process
    if village and village.lower() not in ["all", "none"]:
        stations = [v for v in base_data["Station Name"].unique() if v.lower() == village.lower()]
        if not stations:
            # Fallback to all if specific village not found
            stations = base_data["Station Name"].unique().tolist()
    else:
        stations = base_data["Station Name"].unique().tolist()

    results = []
    
    for station in stations:
        data = base_data[base_data["Station Name"] == station]
        if data.empty:
            continue

        latest = (
            data
            .sort_values("Date")
            .iloc[-1]
        )

        now = datetime.now()

        X = pd.DataFrame([{
            "Latitude": latest["Latitude"],
            "Longitude": latest["Longitude"],
            "Well Depth": latest["Well Depth"],

            "Year": now.year,
            "Month": now.month,

            "State": latest["State"],
            "District": latest["District"],
            "Type of Well": latest["Type of Well"],
            "Aquifer Type": latest["Aquifer Type"],

            "Lag_1": latest["Lag_1"],
            "Lag_2": latest["Lag_2"],
            "Lag_4": latest["Lag_4"],
            "Rolling_4": latest["Rolling_4"]
        }])

        # Type conversion and encoding
        for col in ["State", "District", "Type of Well", "Aquifer Type"]:
            X[col] = encoders[col].transform(X[col])

        prediction = float(model.predict(X)[0])
        current_depth = float(latest["Groundwater_Level"])
        
        score = calculate_health_score(
            current_depth=current_depth,
            predicted_depth=prediction
        )

        results.append({
            "station": station,
            "current_depth": current_depth,
            "predicted_depth": prediction,
            "health_score": score,
            "risk": get_risk(score)
        })

    if not results:
        return None

    # If multiple results (the "All" case), average them
    if len(results) > 1:
        avg_current = sum(r["current_depth"] for r in results) / len(results)
        avg_predicted = sum(r["predicted_depth"] for r in results) / len(results)
        avg_score = sum(r["health_score"] for r in results) / len(results)
        
        return {
            "station": "District Average",
            "current_depth": round(avg_current, 2),
            "predicted_depth": round(avg_predicted, 2),
            "health_score": round(avg_score, 1),
            "risk": get_risk(avg_score)
        }
    
    return results[0]
