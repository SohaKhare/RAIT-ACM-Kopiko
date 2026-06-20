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
* **Example Request**:
  ```bash
  curl "http://localhost:4001/predict?commodity=paddy&state=Maharashtra"
  ```
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
* **Example Request**:
  ```bash
  curl "http://localhost:4001/msp-comparison?commodity=paddy&state=Maharashtra"
  ```
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
* **Example Request**:
  ```bash
  curl "http://localhost:4001/crop-ranking?state=Maharashtra"
  ```
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

Provides direct access to historical/current groundwater levels from the Central Ground Water Board (CGWB) via the IndiaWRIS service or local CSV fallback.

### POST `/groundwater`
* **Description**: Fetch recent groundwater level readings and well depth data.
* **Request Body** (JSON):
  ```json
  {
    "state": "Maharashtra",
    "place": "Pune"
  }
  ```
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/groundwater" \
       -H "Content-Type: application/json" \
       -d '{"state": "Maharashtra", "place": "Pune"}'
  ```
* **Response**:
  ```json
  {
    "statusCode": 200,
    "message": "Data fetched successfully from IndiaWRIS",
    "data": [
      {
        "stationCode": "LOCAL_Name",
        "stationName": "Station Name",
        "stationType": "Ground Water",
        "latitude": null,
        "longitude": null,
        "agencyName": "CGWB",
        "state": "Maharashtra",
        "district": "Pune",
        "majorBasin": null,
        "tributary": null,
        "dataAcquisitionMode": "Manual (CSV Fallback)",
        "stationStatus": "Active",
        "tehsil": "Pune",
        "datatypeCode": "GGZ",
        "description": "Ground Water Level",
        "dataValue": 4.5,
        "dataTime": "2026-06-20T12:00:00",
        "unit": "m",
        "block": null,
        "village": "Village Name",
        "wellType": "Bore Well",
        "wellDepth": 40.0,
        "wellAquiferType": "Unknown"
      }
    ]
  }
  ```

---

## 🏪 3. Mandi Data (AGMARKNET Raw Data)

Fetches raw mandi price and arrival data directly from AGMARKNET listings.

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
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/mandi" \
       -H "Content-Type: application/json" \
       -d '{"state": "Maharashtra", "district": "Kalyan", "market": "Kalyan"}'
  ```
* **Response**:
  ```json
  {
    "resolved_location": {
      "state": "Maharashtra",
      "district": "Thane",
      "market": "Kalyan"
    },
    "api_response": {
      "status": "success",
      "message": "Data fetched successfully.",
      "pagination": {
        "total_count": 1,
        "total_pages": 1,
        "current_page": 1,
        "next_page": null,
        "previous_page": null,
        "items_per_page": 30
      },
      "data": {
        "columns": [
          {
            "key": "commodity_info",
            "columns": [
              { "key": "cmdt_grp_name", "title": "Commodity Group" },
              { "key": "cmdt_name", "title": "Commodity" },
              { "key": "msp_price", "title": "MSP (Rs./Quintal)" }
            ]
          },
          {
            "key": "price_group",
            "title": "Price (Rs./Quintal)",
            "columns": [
              { "key": "as_on_price", "title": "17 Jun, 2026" }
            ]
          }
        ],
        "records": [
          {
            "trend": "up",
            "cmdt_name": "Maize",
            "msp_price": "2400.00",
            "as_on_price": "2700.00",
            "as_on_arrival": "29.90",
            "cmdt_grp_name": "Cereals",
            "reported_date": "17-06-2026",
            "one_day_ago_price": "2700.00",
            "two_day_ago_price": "2700.00",
            "one_day_ago_arrival": "30.70",
            "two_day_ago_arrival": "32.40"
          }
        ]
      }
    }
  }
  ```

---

## 📍 4. Location & Reverse Geocoding

Provides helpers to resolve spatial coordinates into administrative divisions or retrieve registered mandis in a given region.

### POST `/location`
* **Description**: Reverse geocode latitude and longitude to resolve standard state, district, and city names using Nominatim (OpenStreetMap).
* **Request Body** (JSON):
  ```json
  {
    "lat": 19.24,
    "lng": 73.13
  }
  ```
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/location" \
       -H "Content-Type: application/json" \
       -d '{"lat": 19.24, "lng": 73.13}'
  ```
* **Response**:
  ```json
  {
    "city": "Thane",
    "district": "Thane",
    "state": "Maharashtra"
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
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/location/mandis" \
       -H "Content-Type: application/json" \
       -d '{"district": "Thane", "state": "Maharashtra"}'
  ```
* **Response**:
  ```json
  {
    "mandis": [
      "Kalyan",
      "Ulhasnagar",
      "Shahapur"
    ]
  }
  ```

---

## 🌤️ 5. Weather Forecasts

Fetches rainfall insights using Open-Meteo API.

### POST `/weather`
* **Description**: Returns 37 days of daily rainfall records (30 historical days + 7 forecast days) to analyze sowing windows.
* **Request Body** (JSON):
  ```json
  {
    "lat": 19.24,
    "lng": 73.13
  }
  ```
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/weather" \
       -H "Content-Type: application/json" \
       -d '{"lat": 19.24, "lng": 73.13}'
  ```
* **Response**:
  ```json
  {
    "past_30_days": [
      {
        "date": "2026-05-21",
        "precipitation_mm": 0.0
      }
    ],
    "past_30_total_mm": 12.4,
    "forecast_7_days": [
      {
        "date": "2026-06-20",
        "precipitation_mm": 2.5
      }
    ],
    "forecast_7_total_mm": 18.2
  }
  ```

---

## 🤖 6. LLM Conversational Integration

Farmer-facing text and speech translation/conversations using Gemini and Sarvam AI. The system maintains context and invokes tools based on conversation flow.

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
    "district": "Thane",
    "farmer_context": {
      "farmer_name": "Ramesh",
      "preferred_language": "Hindi"
    },
    "conversation_history": []
  }
  ```
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/llm/text" \
       -H "Content-Type: application/json" \
       -d '{"message_text": "Is it good to grow Paddy here?", "language": "Hindi", "lat": 19.24, "lng": 73.13}'
  ```
* **Response**:
  ```json
  {
    "reply_text": "Growing Paddy here requires caution because the groundwater table is moderately depleted. You might want to consider alternative options like Maize or Moong which require less water.",
    "detected_language": "English",
    "missing_fields": ["land_area_acres", "irrigation_source"],
    "updated_context": {
      "farmer_name": "Ramesh",
      "phone_number": null,
      "preferred_language": "Hindi",
      "state_name": "Maharashtra",
      "district_name": "Thane",
      "village_name": null,
      "pincode": null,
      "season": null,
      "land_area_acres": null,
      "irrigation_source": null,
      "current_crop": null,
      "candidate_crop": "paddy"
    },
    "tool_calls": [],
    "switch_to_lang": null
  }
  ```

### POST `/llm/audio`
* **Description**: Handles voice recordings uploaded by farmers, transcribes them, translates, answers, and returns conversational response keys.
* **Request Payload** (Multipart/Form-Data):
  - `file`: Audio file binary (e.g. `.webm`, `.ogg`, `.wav`)
  - `language` (string, optional): Preferred language code.
  - `lat` (float, optional)
  - `lng` (float, optional)
  - `state` (string, optional)
  - `district` (string, optional)
  - `context` (string, optional): JSON-serialized representation of the `farmer_context` dictionary.
  - `history` (string, optional): JSON-serialized list of previous conversational history turns.
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/llm/audio" \
       -F "file=@farmer_voice.webm;type=audio/webm" \
       -F "language=Marathi" \
       -F "lat=19.24" \
       -F "lng=73.13"
  ```
* **Response**:
  ```json
  {
    "reply_text": "भाताची लागवड करण्यासाठी पाण्याची मोठी आवश्यकता असते...",
    "detected_language": "Marathi",
    "missing_fields": ["season", "land_area_acres"],
    "updated_context": {
      "farmer_name": null,
      "phone_number": null,
      "preferred_language": "Marathi",
      "state_name": "Maharashtra",
      "district_name": "Thane",
      "village_name": null,
      "pincode": null,
      "season": null,
      "land_area_acres": null,
      "irrigation_source": null,
      "current_crop": null,
      "candidate_crop": null
    },
    "tool_calls": [
      {
        "id": "call_123xyz",
        "name": "get_groundwater_status",
        "arguments": {
          "state_name": "Maharashtra",
          "district_name": "Thane"
        }
      }
    ],
    "switch_to_lang": null
  }
  ```

---

## 🔄 7. Locational Data Aggregator

Combines groundwater levels (ML-predicted), weather forecasts, mandi arrivals, and crop water requirements in a single high-performance endpoint.

### POST `/aggregator`
* **Description**: Aggregates locational data for a coordinate point.
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
* **Example Request**:
  ```bash
  curl -X POST "http://localhost:4001/aggregator" \
       -H "Content-Type: application/json" \
       -d '{"lat": 19.24, "lng": 73.13, "state": "Maharashtra", "district": "Thane", "mandi": "Kalyan"}'
  ```
* **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "location": {
        "state": "Maharashtra",
        "district": "Thane",
        "mandi": "Kalyan"
      },
      "weather": {
        "past_30_days": [
          { "date": "2026-05-21", "precipitation_mm": 0.0 }
        ],
        "past_30_total_mm": 12.4,
        "forecast_7_days": [
          { "date": "2026-06-20", "precipitation_mm": 2.5 }
        ],
        "forecast_7_total_mm": 18.2
      },
      "groundwater": {
        "station": "Kalyan-East Station",
        "current_depth": 14.5,
        "predicted_depth": 15.2,
        "health_score": 68.2,
        "risk": "Moderate"
      },
      "mandi": [
        {
          "trend": "up",
          "cmdt_name": "Maize",
          "msp_price": "2400.00",
          "as_on_price": "2700.00",
          "as_on_arrival": "29.90",
          "cmdt_grp_name": "Cereals",
          "reported_date": "17-06-2026",
          "one_day_ago_price": "2700.00",
          "two_day_ago_price": "2700.00",
          "one_day_ago_arrival": "30.70",
          "two_day_ago_arrival": "32.40"
        }
      ],
      "soil": {
        "chemistry": {
          "clay": { "value": null, "unit": "%" },
          "nitrogen": { "value": null, "unit": "g/kg" },
          "phh2o": { "value": null, "unit": "-" },
          "sand": { "value": null, "unit": "%" },
          "silt": { "value": null, "unit": "%" },
          "soc": { "value": null, "unit": "g/kg" }
        },
        "moisture_and_temperature": {
          "soil_temperature_c": 26.6,
          "soil_moisture_m3_per_m3": 0.054
        }
      },
      "agriculture_advisory": {
        "groundwater_depth_m": 14.5,
        "groundwater_status": "moderate",
        "ranked_crops": [
          {
            "crop": "Maize",
            "drought_tolerance": "medium",
            "category": "moderate_water",
            "recommendation_score": 100.0
          },
          {
            "crop": "Paddy",
            "drought_tolerance": "low",
            "category": "high_water",
            "recommendation_score": 70.0
          }
        ]
      }
    }
  }
  ```

---

## 8. Utility Endpoints

### GET `/health`
* **Description**: Simple API health check response.
* **Example Request**:
  ```bash
  curl "http://localhost:4001/health"
  ```
* **Response**:
  ```json
  {
    "status": "healthy"
  }
  ```
