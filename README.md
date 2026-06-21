# Bhoomi - Made by Team Kopiko

Welcome to the **Bhoomi** repository! This project is a comprehensive, farmer-facing application designed to empower agricultural decision-making. It features a robust FastAPI-based backend and a Nuxt.js-based frontend.

## What It Does & Why It's Important

At its core, this platform aims to democratize access to agricultural data and predictive insights for farmers, helping them maximize their profits and make informed decisions about which crops to sow and where to sell them.

**Key Capabilities:**
1. **Crop Price Prediction (LightGBM)**: The backend incorporates an ML pipeline trained on historical wholesale market (mandi) data. It predicts future crop prices, allowing farmers to anticipate market trends and secure their income.
2. **Groundwater Health & Risk Forecasting (XGBoost)**: A dedicated XGBoost model analyzes historical Central Ground Water Board (CGWB) data. It predicts future groundwater levels and assigns a Groundwater Health Score with actionable risk categories (Safe, Moderate, High Risk, Critical), advising farmers on water-efficient crop choices.
3. **MSP Comparison & Crop Ranking**: The system compares predicted prices against government Minimum Support Prices (MSP) and ranks crops based on expected profitability and historical price volatility. 
4. **Voice & WhatsApp Accessibility**: Recognizing that digital literacy varies, the platform integrates with Twilio for WhatsApp access and uses Google Gemini for audio transcription. This means farmers can interact with the system using natural voice commands via a familiar chat interface.
5. **Location & Real-Time Market Data**: Using Nominatim for reverse-geocoding and Agmarknet for live market data, the system personalizes recommendations based on the farmer's exact state and district.

By combining advanced predictive analytics with highly accessible interfaces (voice and WhatsApp), this project tackles the critical issue of information asymmetry in agriculture, directly supporting farmer livelihoods.

---

## Project Structure

The repository is organized into the following main directories:

- **`/backend`**: The FastAPI backend service. It houses the ML pipeline, interfaces with external services (Twilio, Gemini, Nominatim, Agmarknet), and uses a Supabase PostgreSQL database.
- **`/kopiko`**: The Nuxt.js frontend application providing the web-based user interface.
- **`/files`**: General project files and assets.

## Backend & ML Architecture

The backend is built with **FastAPI** and includes a complete Data & ML pipeline:

### Machine Learning Pipelines
The project hosts two distinct ML workflows:

**1. Crop Price Predictor (LightGBM):**
- **`data_prep.py`**: Downloads and cleans daily commodity pricing datasets, filtering for standard Kharif crops.
- **`features.py`**: Performs feature engineering, generating time-series features (lags, rolling averages) and joining static MSP data.
- **`train.py`**: Trains the LightGBM regressor using a time-based split to prevent lookahead bias, saving the models for inference.
- **`inference.py`**: Exposes endpoints like `/predict`, `/msp-comparison`, and `/crop-ranking`.

**2. Groundwater Health Monitor (XGBoost):**
- Analyzes CGWB data (2000-2023) across various states, districts, and aquifer types.
- Uses time-series lags and rolling averages combined with geospatial features to train an **XGBoost Regressor**.
- Calculates a custom `Health_Score` and `Risk_Category`, generating actionable insights (e.g., "Groundwater stress detected. Consider water-efficient crops.") based on the model's predictions. Models are exported as `.pkl` artifacts for inference.

### API Architecture
- **`routes/`**: Contains the API routing and endpoints logic.
- **`controllers/`**: Handles the request logic before passing to services.
- **`services/`**: Contains core business logic and external API interactions.
  - `mandi.py`: Queries the Supabase database with hierarchy enforcement and fetches Agmarknet data.
  - `location.py`: Uses the Nominatim API to resolve coordinates.

## Setup and Installation

### Backend (FastAPI & ML)
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment.
3. Install dependencies using `uv` (recommended) or standard pip.
4. Set up environment variables (copy `.env.example` to `.env` and add keys for Twilio, Gemini, Supabase, and Kaggle API for ML data).
5. Run the data prep and training scripts (`python data_prep.py`, `python features.py`, `python train.py`).
6. Run the FastAPI development server: `uvicorn main:app --reload`

### Frontend (Nuxt.js)
1. Navigate to the `kopiko/` directory:
   ```bash
   cd kopiko
   ```
2. Install dependencies using `bun`:
   ```bash
   bun install
   ```
3. Set up environment variables (`cp .env.example .env`).
4. Run the development server:
   ```bash
   bun run dev
   ```

## Technologies Used

- **Machine Learning**: LightGBM, XGBoost, Pandas, Scikit-learn, Parquet, Pickle
- **Backend**: Python, FastAPI, Pydantic, Supabase (PostgreSQL)
- **Frontend**: Nuxt.js, Vue.js, Node.js, Bun
- **External Services**: Twilio (WhatsApp), Google Gemini (Audio Transcription), Nominatim (OpenStreetMap), Agmarknet API, Kaggle API (Datasets)
