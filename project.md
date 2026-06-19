# RAIT-ACM-Kopiko

## Overview
This is a FastAPI-based backend service. It interfaces with external services like Twilio (WhatsApp) and Google Gemini (Audio Transcription).

## Architecture
- `routes/`: Contains the API routing and endpoints logic.
- `services/`: Contains the core business logic (e.g., interacting with external APIs).
- `controllers/`: Contains the controller logic to handle requests before passing to services.
- `data/`: Contains data-related modules.

## Rules
- In services only have business logic.
- In routes directory only have routing not logic.
- In controllers just the controllers part.
