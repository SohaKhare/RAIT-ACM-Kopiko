# Bhoomi Backend API - Kharif Crop Price Prediction & Ranking

This repository contains the Python backend for Bhoomi, a farmer-facing application. This backend handles downloading wholesale agricultural market (mandi) data, processing it, standardizing it, training a LightGBM machine learning model to predict prices, comparing predicted prices to Minimum Support Prices (MSP), and ranking crops.

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) (recommended package manager) or standard `pip`
- Kaggle API token (required to download the market dataset)

### Kaggle API Setup
To download the dataset automatically, make sure your Kaggle credentials are set up. You can generate a new token in your Kaggle Account settings page:
- Option A: Save the `kaggle.json` token file to `~/.kaggle/kaggle.json`.
- Option B: Export environment variables in your terminal:
  ```bash
  export KAGGLE_USERNAME="your-username"
  export KAGGLE_KEY="your-api-key"
  ```

### Install Dependencies
If using `uv`:
```bash
uv sync
```

If using standard `pip`:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Data & Model Pipeline

The backend includes a step-by-step pipeline to process data and train the prediction model:

### Step 1 & 2: Data Acquisition, Inspection, & Cleaning
Downloads only the 2025 and 2026 yearly market files from the Kaggle dataset (`khandelwalmanas/daily-commodity-prices-india`), filters them to the 14 standard Kharif crops, cleans zero or negative prices, standardizes dates, and saves a cleaned parquet file:
```bash
python data_prep.py
```
*Cleaned data is saved to `data/cleaned_market_data.parquet` (~3.8 MB).*

### Step 3: Feature Engineering
Aggregates prices to the `(Commodity, State, Date)` level, aligns dates into a continuous daily grid per active group, forward-fills gaps, and generates time-series features (lags, rolling averages, calendar details) and joins static MSP data:
```bash
python features.py
```
*Features are saved to `data/feature_engineered_data.parquet`.*

### Step 4: Model Training
Trains a LightGBM regressor using a time-based train/test split (80/20 based on unique dates to prevent lookahead bias). It prints evaluation metrics (MAPE overall and per-crop) and saves the model and encoders:
```bash
python train.py
```
*Saved artifacts:*
- `data/mandi_model.joblib` (LightGBM model)
- `data/le_commodity.joblib` (Commodity label encoder)
- `data/le_state.joblib` (State label encoder)

---

## ⚡ Running the FastAPI Backend

To start the local FastAPI web server:
```bash
uvicorn main:app --reload --port 4001
```

Once running, you can open http://127.0.0.1:4001/docs in your browser to view the interactive Swagger API documentation.

---

## 🔌 API Endpoints Reference

### 1. Predict Price
* **Endpoint**: `GET /predict`
* **Query Parameters**:
  - `commodity` (string, required): e.g. `paddy`, `maize`, `cotton`
  - `state` (string, required): e.g. `Maharashtra`, `Punjab`
  - `date` (string, optional): Date in format `YYYY-MM-DD`. Defaults to the latest date in the dataset.
* **Example Request**:
  ```bash
  curl "http://127.0.0.1:4001/predict?commodity=paddy&state=Maharashtra"
  ```
* **Example Response**:
  ```json
  {
    "commodity": "paddy",
    "state": "Maharashtra",
    "date": "2026-04-20",
    "predicted_price": 2720.02
  }
  ```

### 2. MSP Comparison
* **Endpoint**: `GET /msp-comparison`
* **Query Parameters**:
  - `commodity` (string, required): Crop name
  - `state` (string, required): State name
* **Example Request**:
  ```bash
  curl "http://127.0.0.1:4001/msp-comparison?commodity=paddy&state=Maharashtra"
  ```
* **Example Response**:
  ```json
  {
    "commodity": "paddy",
    "state": "Maharashtra",
    "date": "2026-04-20",
    "predicted_price": 2720.02,
    "msp": 2369.0,
    "gap_pct": 14.82
  }
  ```

### 3. Crop Ranking
* **Endpoint**: `GET /crop-ranking`
* **Query Parameters**:
  - `state` (string, required): State name
  - `volatility_weight` (float, optional): Penalty factor for price volatility. Defaults to `50.0`.
* **Example Request**:
  ```bash
  curl "http://127.0.0.1:4001/crop-ranking?state=Maharashtra"
  ```
* **Example Response**:
  ```json
  {
    "state": "Maharashtra",
    "volatility_weight": 50.0,
    "ranking": [
      {
        "crop": "paddy",
        "predicted_price": 2720.02,
        "msp": 2369.0,
        "gap_pct": 14.82,
        "volatility_level": "Medium",
        "historical_volatility": 11.78,
        "score": 8.93
      },
      {
        "crop": "ragi",
        "predicted_price": 5413.88,
        "msp": 4886.0,
        "gap_pct": 10.8,
        "volatility_level": "Medium",
        "historical_volatility": 5.53,
        "score": 8.04
      }
    ]
  }
  ```
