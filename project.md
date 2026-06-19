# RAIT-ACM-Kopiko

## Overview
This is a FastAPI-based backend service. It interfaces with external services like Twilio (WhatsApp) and Google Gemini (Audio Transcription), and uses a Supabase PostgreSQL database for structured data.

## Architecture
- `routes/`: Contains the API routing and endpoints logic.
- `services/`: Contains the core business logic (e.g., interacting with external APIs, Nominatim reverse geocoding).
- `controllers/`: Contains the controller logic to handle requests before passing to services.
- `data/`: Contains database migration scripts and data seeding utilities.
- `models/`: Contains Pydantic models for request/response schemas.

## Rules
- In services only have business logic.
- In routes directory only have routing not logic.
- In controllers just the controllers part.
