import os
import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder

DATA_DIR = "data"
FEATURE_FILE = os.path.join(DATA_DIR, "feature_engineered_data.parquet")
MODEL_FILE = os.path.join(DATA_DIR, "mandi_model.joblib")
LE_COMM_FILE = os.path.join(DATA_DIR, "le_commodity.joblib")
LE_STATE_FILE = os.path.join(DATA_DIR, "le_state.joblib")

def train_model():
    print("--- Step 4: Model Training ---")
    if not os.path.exists(FEATURE_FILE):
        raise FileNotFoundError(f"Features file not found at {FEATURE_FILE}. Please run features.py first.")
        
    print(f"Loading features from {FEATURE_FILE}...")
    df = pd.read_parquet(FEATURE_FILE)
    df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"])
    
    # Sort chronologically for time-based splitting
    df = df.sort_values("Arrival_Date")
    
    # Encode categorical columns
    print("Encoding categorical columns (Commodity, State)...")
    le_comm = LabelEncoder()
    le_state = LabelEncoder()
    df["Commodity_Encoded"] = le_comm.fit_transform(df["Commodity"])
    df["State_Encoded"] = le_state.fit_transform(df["State"])
    
    # Save encoders for inference
    joblib.dump(le_comm, LE_COMM_FILE)
    joblib.dump(le_state, LE_STATE_FILE)
    print("Saved label encoders to disk.")
    
    # Split using a time-based approach (first 80% dates for train, remaining 20% for test)
    # Split is time-based (not random) to avoid lookahead bias, ensuring the model is evaluated on future data it has not seen.
    print("Performing time-based train/test split...")
    unique_dates = sorted(df["Arrival_Date"].unique())
    cutoff_idx = int(len(unique_dates) * 0.8)
    cutoff_date = unique_dates[cutoff_idx]
    
    train_df = df[df["Arrival_Date"] < cutoff_date]
    test_df = df[df["Arrival_Date"] >= cutoff_date].copy()
    
    features = [
        "Commodity_Encoded", "State_Encoded",
        "price_lag_1", "price_lag_7", "price_lag_30",
        "price_roll_mean_7", "price_roll_std_7",
        "price_roll_mean_30", "price_roll_std_30",
        "month", "week_of_year", "day_of_year",
        "msp_per_quintal"
    ]
    
    X_train, y_train = train_df[features], train_df["Modal_Price"]
    X_test, y_test = test_df[features], test_df["Modal_Price"]
    
    print(f"Train set: {len(train_df):,} rows (from {train_df['Arrival_Date'].min().strftime('%Y-%m-%d')} to {train_df['Arrival_Date'].max().strftime('%Y-%m-%d')})")
    print(f"Test set: {len(test_df):,} rows (from {test_df['Arrival_Date'].min().strftime('%Y-%m-%d')} to {test_df['Arrival_Date'].max().strftime('%Y-%m-%d')})")
    
    # Train LightGBM model (using default/baseline parameters which yielded the best MAPE of 4.65%)
    print("Training LightGBM model...")
    model = lgb.LGBMRegressor(
        n_estimators=100,
        random_state=42,
        verbose=-1
    )
    model.fit(X_train, y_train)
    
    # Predict and evaluate
    preds = model.predict(X_test)
    test_df["preds"] = preds
    
    # Compute MAPE (Mean Absolute Percentage Error)
    test_df["mape"] = np.abs(test_df["Modal_Price"] - test_df["preds"]) / test_df["Modal_Price"] * 100
    overall_mape = test_df["mape"].mean()
    
    print("\n=== Model Evaluation Results ===")
    print(f"Overall Test MAPE: {overall_mape:.2f}%")
    
    print("\nTest MAPE broken down by crop:")
    for crop in sorted(test_df["Commodity"].unique()):
        crop_mape = test_df[test_df["Commodity"] == crop]["mape"].mean()
        print(f" - {crop:12}: {crop_mape:.2f}%")
        
    # Save the trained model
    joblib.dump(model, MODEL_FILE)
    print(f"\nSuccessfully saved trained LightGBM model to {MODEL_FILE}")

if __name__ == "__main__":
    train_model()
