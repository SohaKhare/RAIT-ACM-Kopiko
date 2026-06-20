# Bhoomi Backend API Reference

This document serves as the complete REST API specification for the Bhoomi backend. It outlines all available endpoints, request bodies, query parameters, and example responses.

---

## 🌾 1. Mandi Price Prediction & Crop Ranking

These endpoints provide machine-learning-based price predictions for the 14 Kharif crops, compare predicted prices against Minimum Support Price (MSP), and rank crops by profit margin and volatility.

### GET `/predict`
* **Description**: Returns the predicted modal price for a single crop, state, and date.
* **Query Parameters**:
  - `commodity` (string, required): One of the 14 Kharif crops (`paddy`, `jowar`, `bajra`, `maize`, `ragi`, `tur/arhar`, `moong`, `urad`, `groundnut`, `soybean`, `sesamum`, `sunflower`, `nigerseed`, `cotton`).
  - `state` (string, required): State name (case-insensitive).
  - `date` (string, optional): Date in `YYYY-MM-DD` format. Defaults to the latest available dataset date.
* **Response**:
  ```json
  {
    "commodity": "paddy",
    "state": "Maharashtra",
    "date": "2026-04-20",
    "predicted_price": 2720.02
  }
  ```

### GET `/msp-comparison`
* **Description**: Compares the predicted crop price against the official Minimum Support Price (MSP) and returns the price difference percentage.
* **Query Parameters**:
  - `commodity` (string, required): Kharif crop name.
  - `state` (string, required): State name.
* **Response**:
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

### GET `/crop-ranking`
* **Description**: Returns the ranked list of all 14 Kharif crops for a state. Ranks crops using `score = gap_pct - (volatility_weight * normalized_std)` (expected margin penalized by price risk).
* **Query Parameters**:
  - `state` (string, required): State name.
  - `volatility_weight` (float, optional): Penalty multiplier for price volatility. Defaults to `50.0`.
* **Response**:
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
      }
    ]
  }
  ```

---

## 💧 2. Groundwater Information

### POST `/groundwater`
* **Description**: Fetch recent groundwater level readings and well depth data.
* **Request Body** (JSON):
  ```json
  {
    "state": "Maharashtra",
    "place": "Pune"
  }
  ```
* **Response**: Locational groundwater statistics (station name, well depth, and latest water table reading).

---

## 🏪 3. Mandi Data (AGMARKNET Raw Data)

### POST `/mandi`
* **Description**: Fetch raw mandi price/arrival data from standard AGMARKNET listings.
* **Request Body** (JSON):
  ```json
  {
    "state": "Maharashtra",
    "district": "Kalyan",
    "market": "Kalyan"
  }
  ```

---

## 📍 4. Location & Reverse Geocoding

### POST `/location`
* **Description**: Reverse geocode latitude and longitude to resolve standard state, district, and city names.
* **Request Body** (JSON):
  ```json
  {
    "lat": 19.24,
    "lng": 73.13
  }
  ```

### POST `/location/mandis`
* **Description**: Returns all registered markets (mandis) in a given district.
* **Request Body** (JSON):
  ```json
  {
    "district": "Thane",
    "state": "Maharashtra"
  }
  ```
* **Response**:
  ```json
  {
    "mandis": ["Kalyan", "Ulhasnagar", "Shahapur"]
  }
  ```

---

## 🌤️ 5. Weather Forecasts

### POST `/weather`
* **Description**: Returns 37 days of daily rainfall records (30 historical days + 7 forecast days) to analyze sowing windows.
* **Request Body** (JSON):
  ```json
  {
    "lat": 19.24,
    "lng": 73.13
  }
  ```

---

## 🤖 6. LLM Conversational Integration

Farmer-facing text and speech translation/conversations using Gemini and Sarvam AI.

### POST `/llm/text`
* **Description**: Handles a query message from a farmer and translates/answers using LLM contexts.
* **Request Body** (JSON):
  ```json
  {
    "message_text": "Is it good to grow Paddy here?",
    "language": "Hindi",
    "lat": 19.24,
    "lng": 73.13,
    "state": "Maharashtra",
    "district": "Thane"
  }
  ```

### POST `/llm/audio`
* **Description**: Handles voice recordings uploaded by farmers, transcribes them, translates to English, answers, and responds.
* **Request Payload** (Multipart/Form-Data):
  - `file`: Audio file binary (e.g. `.webm`, `.ogg`)
  - `language` (string, optional)
  - `lat` (float, optional)
  - `lng` (float, optional)
  - `state` (string, optional)
  - `district` (string, optional)

---

## 🔄 7. Locational Data Aggregator

### POST `/aggregator`
* **Description**: Aggregates locational data (groundwater, weather, mandi listings) for a coordinate point in a single call.
* **Request Body** (JSON):
  ```json
  {
    "lat": 19.24,
    "lng": 73.13,
    "state": "Maharashtra",
    "district": "Thane",
    "mandi": "Kalyan"
  }
  ```

---

## 🩺 8. Utility Endpoints

### GET `/health`
* **Description**: Simple API health check response.
* **Response**:
  ```json
  {
    "status": "healthy"
  }
  ```
