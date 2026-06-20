import os
import joblib
import numpy as np
import pandas as pd

DATA_DIR = "data"
MODEL_FILE = os.path.join(DATA_DIR, "mandi_model.joblib")
LE_COMM_FILE = os.path.join(DATA_DIR, "le_commodity.joblib")
LE_STATE_FILE = os.path.join(DATA_DIR, "le_state.joblib")
CLEANED_DATA_FILE = os.path.join(DATA_DIR, "cleaned_market_data.parquet")
MSP_FILE = os.path.join(DATA_DIR, "msp_kharif.csv")

# Global variables to cache model and encoders in memory
_MODEL = None
_LE_COMM = None
_LE_STATE = None
_CLEANED_DF = None
_MSP_DF = None

def load_artifacts():
    """
    Load machine learning model, preprocessors, and datasets into memory once.
    """
    global _MODEL, _LE_COMM, _LE_STATE, _CLEANED_DF, _MSP_DF
    if _MODEL is None:
        if not os.path.exists(MODEL_FILE):
            raise FileNotFoundError(f"Model file not found at {MODEL_FILE}. Please run train.py first.")
        _MODEL = joblib.load(MODEL_FILE)
        _LE_COMM = joblib.load(LE_COMM_FILE)
        _LE_STATE = joblib.load(LE_STATE_FILE)
        
        # Load datasets
        _CLEANED_DF = pd.read_parquet(CLEANED_DATA_FILE)
        _CLEANED_DF["Arrival_Date"] = pd.to_datetime(_CLEANED_DF["Arrival_Date"])
        
        _MSP_DF = pd.read_csv(MSP_FILE)
        _MSP_DF["crop_name"] = _MSP_DF["crop_name"].str.strip().str.lower()
        
    return _MODEL, _LE_COMM, _LE_STATE, _CLEANED_DF, _MSP_DF

def get_latest_date_in_dataset():
    """
    Helper to find the most recent date available in our market dataset.
    """
    _, _, _, df_clean, _ = load_artifacts()
    return df_clean["Arrival_Date"].max()

def get_crop_list():
    """
    Get the list of the 14 standard Kharif crops from the MSP file.
    """
    _, _, _, _, msp_df = load_artifacts()
    return msp_df["crop_name"].unique().tolist()

def get_state_list():
    """
    Get the list of valid states present in our dataset.
    """
    _, _, _, df_clean, _ = load_artifacts()
    return sorted(df_clean["State"].unique().tolist())

def construct_features(commodity: str, state: str, target_date: pd.Timestamp):
    """
    Constructs the feature vector for a given crop/state/date by using historical daily data.
    Ensures no lookahead bias by shifting and computing rolling windows backward from target_date.
    """
    model, le_comm, le_state, df_clean, msp_df = load_artifacts()
    
    # 1. Filter for commodity & state
    df_group = df_clean[(df_clean["Commodity"] == commodity) & (df_clean["State"] == state)]
    if df_group.empty:
        return None
        
    # 2. Aggregate to daily frequency
    df_agg = df_group.groupby("Arrival_Date")["Modal_Price"].mean().reset_index().sort_values("Arrival_Date")
    min_date = df_agg["Arrival_Date"].min()
    
    # If target_date is before our data starts, we can't build lag features
    if target_date <= min_date:
        return None
        
    # 3. Create continuous daily range from start to target_date, then forward-fill
    date_range = pd.date_range(min_date, target_date, freq="D")
    df_grid = pd.DataFrame({"Arrival_Date": date_range})
    df_merged = pd.merge(df_grid, df_agg, on="Arrival_Date", how="left")
    df_merged["Modal_Price"] = df_merged["Modal_Price"].ffill()
    
    # 4. Generate Lags (1, 7, 30 days)
    df_merged["price_lag_1"] = df_merged["Modal_Price"].shift(1)
    df_merged["price_lag_7"] = df_merged["Modal_Price"].shift(7)
    df_merged["price_lag_30"] = df_merged["Modal_Price"].shift(30)
    
    # 5. Generate Rolling features on lag_1 (yesterday backward) to avoid lookahead bias
    df_merged["price_roll_mean_7"] = df_merged["price_lag_1"].rolling(7, min_periods=1).mean()
    df_merged["price_roll_std_7"] = df_merged["price_lag_1"].rolling(7, min_periods=1).std().fillna(0.0)
    df_merged["price_roll_mean_30"] = df_merged["price_lag_1"].rolling(30, min_periods=1).mean()
    df_merged["price_roll_std_30"] = df_merged["price_lag_1"].rolling(30, min_periods=1).std().fillna(0.0)
    
    # Extract the target date row (which is the last row)
    target_row = df_merged.iloc[-1].copy()
    if pd.isna(target_row["price_lag_1"]) or pd.isna(target_row["price_lag_7"]) or pd.isna(target_row["price_lag_30"]):
        # Lags are undefined (not enough history yet)
        return None
        
    # 6. Add calendar features
    target_row["month"] = target_date.month
    target_row["week_of_year"] = int(target_date.isocalendar()[1])
    target_row["day_of_year"] = target_date.dayofyear
    target_row["year"] = target_date.year
    
    # 7. Add static MSP
    msp_val = msp_df[(msp_df["crop_name"] == commodity) & (msp_df["year"] == target_date.year)]["msp_per_quintal"].values
    if len(msp_val) > 0:
        target_row["msp_per_quintal"] = msp_val[0]
    else:
        # Fallback to latest available year for the crop if exact year is missing
        crop_msp = msp_df[msp_df["crop_name"] == commodity].sort_values("year", ascending=False)
        target_row["msp_per_quintal"] = crop_msp.iloc[0]["msp_per_quintal"] if not crop_msp.empty else np.nan
        
    # 8. Encode categorical features
    try:
        target_row["Commodity_Encoded"] = le_comm.transform([commodity])[0]
        target_row["State_Encoded"] = le_state.transform([state])[0]
    except ValueError:
        # Out-of-vocabulary state or commodity
        return None
        
    return target_row

def predict_crop_price(commodity: str, state: str, target_date_str: str = None) -> float:
    """
    Generate price prediction for a single crop/state/date.
    If target_date_str is omitted, defaults to the latest date available in the dataset.
    """
    model, le_comm, le_state, _, _ = load_artifacts()
    
    # Resolve target date
    if target_date_str is None:
        target_date = get_latest_date_in_dataset()
    else:
        target_date = pd.to_datetime(target_date_str)
        
    # Construct features
    feat_row = construct_features(commodity, state, target_date)
    if feat_row is None:
        raise ValueError(f"Insufficient historical data to predict price for {commodity} in {state} on {target_date.strftime('%Y-%m-%d')}")
        
    features_list = [
        "Commodity_Encoded", "State_Encoded",
        "price_lag_1", "price_lag_7", "price_lag_30",
        "price_roll_mean_7", "price_roll_std_7",
        "price_roll_mean_30", "price_roll_std_30",
        "month", "week_of_year", "day_of_year",
        "msp_per_quintal"
    ]
    
    X = pd.DataFrame([feat_row[features_list]])
    pred_price = model.predict(X)[0]
    return float(pred_price)

def get_msp_gap_comparison(commodity: str, state: str) -> dict:
    """
    Compares predicted price against MSP and returns predicted price, MSP, and gap %.
    Defaults to the latest date in the dataset.
    """
    model, le_comm, le_state, df_clean, msp_df = load_artifacts()
    ref_date = get_latest_date_in_dataset()
    
    pred_price = predict_crop_price(commodity, state, ref_date)
    
    # Find MSP
    msp_val = msp_df[(msp_df["crop_name"] == commodity) & (msp_df["year"] == ref_date.year)]["msp_per_quintal"].values
    if len(msp_val) > 0:
        msp = float(msp_val[0])
    else:
        crop_msp = msp_df[msp_df["crop_name"] == commodity].sort_values("year", ascending=False)
        msp = float(crop_msp.iloc[0]["msp_per_quintal"]) if not crop_msp.empty else 0.0
        
    gap_pct = ((pred_price - msp) / msp * 100) if msp > 0 else 0.0
    
    return {
        "commodity": commodity,
        "state": state,
        "date": ref_date.strftime("%Y-%m-%d"),
        "predicted_price": round(pred_price, 2),
        "msp": round(msp, 2),
        "gap_pct": round(gap_pct, 2)
    }

def get_crop_ranking(state: str, volatility_weight: float = 50.0) -> list:
    """
    Ranks the 14 kharif crops for a given state.
    Favors crops with predicted price > MSP (higher gap_pct) and penalizes high price volatility.
    Score = gap_pct - (volatility_weight * normalized_std)
    """
    _, _, _, df_clean, msp_df = load_artifacts()
    ref_date = get_latest_date_in_dataset()
    
    crops = get_crop_list()
    ranked_list = []
    
    for crop in crops:
        # Check if the crop has active transactions in this state
        df_crop_state = df_clean[(df_clean["Commodity"] == crop) & (df_clean["State"] == state)]
        if df_crop_state.empty:
            continue
            
        # 1. Historical Volatility (normalized standard deviation / Coefficient of Variation)
        prices = df_crop_state["Modal_Price"]
        if len(prices) < 5:
            continue
        mean_price = prices.mean()
        std_price = prices.std()
        normalized_std = std_price / mean_price if mean_price > 0 else 0.0
        
        # Volatility level classification
        if normalized_std <= 0.05:
            vol_level = "Low"
        elif normalized_std <= 0.15:
            vol_level = "Medium"
        else:
            vol_level = "High"
            
        # 2. Predicted Price
        try:
            pred_price = predict_crop_price(crop, state, ref_date)
        except Exception:
            # Skip crops with insufficient history to build features on this date
            continue
            
        # 3. MSP Gap Calculation
        msp_val = msp_df[(msp_df["crop_name"] == crop) & (msp_df["year"] == ref_date.year)]["msp_per_quintal"].values
        if len(msp_val) > 0:
            msp = float(msp_val[0])
        else:
            crop_msp = msp_df[msp_df["crop_name"] == crop].sort_values("year", ascending=False)
            msp = float(crop_msp.iloc[0]["msp_per_quintal"]) if not crop_msp.empty else 0.0
            
        gap_pct = ((pred_price - msp) / msp * 100) if msp > 0 else 0.0
        
        # 4. Combined scoring
        score = gap_pct - (volatility_weight * normalized_std)
        
        ranked_list.append({
            "crop": crop,
            "predicted_price": round(pred_price, 2),
            "msp": round(msp, 2),
            "gap_pct": round(gap_pct, 2),
            "volatility_level": vol_level,
            "historical_volatility": round(normalized_std * 100, 2),  # in percentage format
            "score": round(score, 2)
        })
        
    # Sort crops descending by score
    ranked_list = sorted(ranked_list, key=lambda x: x["score"], reverse=True)
    return ranked_list
