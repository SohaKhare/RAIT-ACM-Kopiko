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

    data = history_df[
        (history_df["State"].str.lower() == state.lower())
        &
        (history_df["District"].str.lower() == district.lower())
    ]

    if data.empty:
        return None

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

    X["State"] = encoders[
        "State"
    ].transform(X["State"])

    X["District"] = encoders[
        "District"
    ].transform(X["District"])

    X["Type of Well"] = encoders[
        "Type of Well"
    ].transform(X["Type of Well"])

    X["Aquifer Type"] = encoders[
        "Aquifer Type"
    ].transform(X["Aquifer Type"])

    prediction = float(
        model.predict(X)[0]
    )

    current_depth = float(
        latest["Groundwater_Level"]
    )

    score = calculate_health_score(
        current_depth,
        prediction
    )

    risk = get_risk(score)

    return {
        "station": latest["Station Name"],
        "current_depth": round(
            current_depth,
            2
        ),
        "predicted_depth": round(
            prediction,
            2
        ),
        "health_score": score,
        "risk": risk
    }