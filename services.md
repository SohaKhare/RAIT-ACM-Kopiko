# Services Architecture

## Overview
This document outlines the services used within the RAIT-ACM-Kopiko project.

## Services
1. `mandi.py`: Accepts a location string (English). Searches market-data.json → district-data.json → state-data.json (hierarchy: market → district → state). Resolves IDs, calls Agmarknet API, and returns data with `resolved_location` metadata (matched_level, state, district, market names).

## Principles
- All new external API integrations and core business logic must be placed here.
- Services should return data structures (e.g., JSON dicts) ready for the controllers/routes.
