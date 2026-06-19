# Services Architecture

## Overview
This document outlines the services used within the RAIT-ACM-Kopiko project.

## Services
1. `mandi.py`: Accepts structured optional inputs (`state`, `district`, `market`). Queries the Supabase database with hierarchy enforcement (market → district → state) to resolve location IDs. Calls the Agmarknet API, and returns data with `resolved_location` metadata (matched_level, state, district, market names).
2. `location.py`: Accepts latitude and longitude. Uses the Nominatim (OpenStreetMap) free reverse geocoding API to resolve coordinates into city, district, and state strings.

## Principles
- All new external API integrations and core business logic must be placed here.
- Services should return data structures (e.g., JSON dicts) ready for the controllers/routes.
