import os
import pandas as pd
import numpy as np

DATA_DIR = "data"
CLEANED_FILE = os.path.join(DATA_DIR, "cleaned_market_data.parquet")
FEATURE_FILE = os.path.join(DATA_DIR, "feature_engineered_data.parquet")
MSP_FILE = os.path.join(DATA_DIR, "msp_kharif.csv")

def run_feature_engineering():
    print("--- Step 3: Feature Engineering ---")
    if not os.path.exists(CLEANED_FILE):
        raise FileNotFoundError(f"Cleaned data file not found at {CLEANED_FILE}. Please run data_prep.py first.")
    if not os.path.exists(MSP_FILE):
        raise FileNotFoundError(f"MSP CSV file not found at {MSP_FILE}.")
        
    print(f"Loading cleaned market data from {CLEANED_FILE}...")
    df = pd.read_parquet(CLEANED_FILE)
    df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"])
    
    # 1. Aggregate to (Commodity, State, Date) level by taking the mean of Modal_Price
    print("Aggregating prices to (Commodity, State, Date) level...")
    df_agg = df.groupby(["Commodity", "State", "Arrival_Date"])["Modal_Price"].mean().reset_index()
    df_agg = df_agg.sort_values(by=["Commodity", "State", "Arrival_Date"])
    
    # 2. Reindex each active group to a continuous daily frequency
    print("Creating daily time-series grid for active groups...")
    active_pairs = df_agg[["Commodity", "State"]].drop_duplicates()
    overall_dates = pd.date_range(df_agg["Arrival_Date"].min(), df_agg["Arrival_Date"].max(), freq="D")
    dates_df = pd.DataFrame({"Arrival_Date": overall_dates})
    df_grid = active_pairs.merge(dates_df, how="cross")
    
    # Merge and sort
    df_merged = pd.merge(df_grid, df_agg, on=["Commodity", "State", "Arrival_Date"], how="left")
    df_merged = df_merged.sort_values(by=["Commodity", "State", "Arrival_Date"])
    
    # 3. Forward-fill prices within each (Commodity, State) group
    print("Forward-filling prices to fill daily gaps...")
    df_merged["Modal_Price"] = df_merged.groupby(["Commodity", "State"])["Modal_Price"].ffill()
    
    # 4. Generate Lag features (1 day, 7 days, 30 days)
    print("Generating lag features (1, 7, 30 days)...")
    df_merged["price_lag_1"] = df_merged.groupby(["Commodity", "State"])["Modal_Price"].shift(1)
    df_merged["price_lag_7"] = df_merged.groupby(["Commodity", "State"])["Modal_Price"].shift(7)
    df_merged["price_lag_30"] = df_merged.groupby(["Commodity", "State"])["Modal_Price"].shift(30)
    
    # 5. Generate Rolling features (7-day and 30-day mean/std of price)
    # To prevent lookahead bias, compute these on price_lag_1 (yesterday's price backward)
    print("Generating rolling features (7-day and 30-day mean & std)...")
    df_merged["price_roll_mean_7"] = df_merged.groupby(["Commodity", "State"])["price_lag_1"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )
    df_merged["price_roll_std_7"] = df_merged.groupby(["Commodity", "State"])["price_lag_1"].transform(
        lambda x: x.rolling(7, min_periods=1).std()
    )
    df_merged["price_roll_mean_30"] = df_merged.groupby(["Commodity", "State"])["price_lag_1"].transform(
        lambda x: x.rolling(30, min_periods=1).mean()
    )
    df_merged["price_roll_std_30"] = df_merged.groupby(["Commodity", "State"])["price_lag_1"].transform(
        lambda x: x.rolling(30, min_periods=1).std()
    )
    
    # Fill rolling std NaNs with 0 (occurs when there's only 1 observation in rolling window)
    df_merged["price_roll_std_7"] = df_merged["price_roll_std_7"].fillna(0.0)
    df_merged["price_roll_std_30"] = df_merged["price_roll_std_30"].fillna(0.0)
    
    # 6. Calendar features (month, week-of-year, day-of-year)
    print("Generating calendar features...")
    df_merged["month"] = df_merged["Arrival_Date"].dt.month
    df_merged["week_of_year"] = df_merged["Arrival_Date"].dt.isocalendar().week.astype(int)
    df_merged["day_of_year"] = df_merged["Arrival_Date"].dt.dayofyear
    df_merged["year"] = df_merged["Arrival_Date"].dt.year
    
    # 7. Join MSP as static feature per (commodity, year)
    print("Joining MSP static feature...")
    msp_df = pd.read_csv(MSP_FILE)
    msp_df["crop_name"] = msp_df["crop_name"].str.strip().str.lower()
    df_merged["crop_key"] = df_merged["Commodity"].str.strip().str.lower()
    
    df_merged = pd.merge(
        df_merged,
        msp_df,
        left_on=["crop_key", "year"],
        right_on=["crop_name", "year"],
        how="left"
    )
    
    # Clean up intermediate keys
    df_merged = df_merged.drop(columns=["crop_key", "crop_name"])
    
    # 8. Drop rows where lag features are undefined (e.g. at the start of each group's time series)
    print("Dropping rows with undefined lag features...")
    df_features = df_merged.dropna(subset=["Modal_Price", "price_lag_1", "price_lag_7", "price_lag_30"])
    
    print(f"Saving feature-engineered dataset to {FEATURE_FILE}...")
    df_features.to_parquet(FEATURE_FILE, index=False)
    print(f"Feature engineering complete! Total records saved: {len(df_features):,}")

if __name__ == "__main__":
    run_feature_engineering()
