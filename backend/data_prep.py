import os
import subprocess
import polars as pl

RAW_DIR = "data"
RAW_SUBDIR = "data/raw"
FILE_2025 = os.path.join(RAW_SUBDIR, "2025.parquet")
FILE_2026 = os.path.join(RAW_SUBDIR, "2026.parquet")
CLEANED_FILE = os.path.join(RAW_DIR, "cleaned_market_data.parquet")

CROP_MAPPING = {
    'Paddy (Dhan)(Common)': 'paddy',
    'Paddy (Common)': 'paddy',
    'Jowar (Sorghum)': 'jowar',
    'Bajra (Pearl Millet/Cumbu)': 'bajra',
    'Maize': 'maize',
    'Ragi (Finger Millet)': 'ragi',
    'Arhar (Tur/Red Gram)(Whole)': 'tur/arhar',
    'Green Gram (Moong)(Whole)': 'moong',
    'Black Gram (Urd Beans)(Whole)': 'urad',
    'Groundnut': 'groundnut',
    'Soyabean': 'soybean',
    'Sesamum (Sesame,Gingelly,Til)': 'sesamum',
    'Sunflower': 'sunflower',
    'Niger Seed (Ramtil)': 'nigerseed',
    'Cotton': 'cotton'
}

def download_if_missing(file_path, remote_name):
    if not os.path.exists(file_path):
        print(f"Downloading {remote_name} to {RAW_SUBDIR}...")
        cmd = [
            ".venv/bin/kaggle", "datasets", "download",
            "-d", "khandelwalmanas/daily-commodity-prices-india",
            "-f", remote_name,
            "-p", RAW_SUBDIR
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to download {remote_name}: {result.stderr}")
        print(f"Successfully downloaded {remote_name}")
    else:
        print(f"{file_path} already exists. Skipping download.")

def load_raw_data():
    os.makedirs(RAW_SUBDIR, exist_ok=True)
    download_if_missing(FILE_2025, "parquet/2025.parquet")
    download_if_missing(FILE_2026, "parquet/2026.parquet")
    
    print("Loading raw files...")
    df_2025 = pl.read_parquet(FILE_2025)
    df_2026 = pl.read_parquet(FILE_2026)
    return pl.concat([df_2025, df_2026])

def clean_and_save():
    df = load_raw_data()
    n_original = len(df)
    
    print("\n--- Step 2: Filtering and Cleaning ---")
    
    # 1. Filter commodities
    print("Filtering to 14 kharif crops...")
    df_filtered = df.filter(pl.col("Commodity").is_in(list(CROP_MAPPING.keys())))
    n_filtered = len(df_filtered)
    print(f"Dropped {n_original - n_filtered:,} rows belonging to non-kharif crops.")
    
    # 2. Map commodities to standardized names
    df_mapped = df_filtered.with_columns(
        pl.col("Commodity").replace(CROP_MAPPING).alias("Commodity")
    )
    
    # 3. Clean invalid prices (<= 0)
    print("Cleaning price fields (dropping <= 0)...")
    invalid_mask = (
        (pl.col("Min_Price") <= 0) | 
        (pl.col("Max_Price") <= 0) | 
        (pl.col("Modal_Price") <= 0)
    )
    n_invalid = df_mapped.filter(invalid_mask).height
    df_cleaned = df_mapped.filter(~invalid_mask)
    print(f"Dropped {n_invalid:,} rows with missing, zero, or negative prices.")
    
    # 4. Standardize Date format & type
    print("Standardizing dates...")
    df_cleaned = df_cleaned.with_columns(
        pl.col("Arrival_Date").str.to_date("%Y-%m-%d").alias("Arrival_Date")
    )
    
    # 5. Sort by commodity + state + date
    print("Sorting by commodity, state, and date...")
    df_sorted = df_cleaned.sort(["Commodity", "State", "Arrival_Date"])
    
    # Save output
    print(f"Saving cleaned dataset to {CLEANED_FILE}...")
    df_sorted.write_parquet(CLEANED_FILE)
    print(f"Cleaned dataset saved successfully! Total rows: {df_sorted.height:,}")
    
    # Print file size info
    size_mb = os.path.getsize(CLEANED_FILE) / (1024 * 1024)
    print(f"Cleaned Parquet File Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    clean_and_save()
