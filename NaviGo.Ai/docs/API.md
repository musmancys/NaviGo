# NaviGo API Documentation

The NaviGo API is a production-grade FastAPI service providing multimodal AI, tourism databases, spatial searches, and real-time travel updates for Northern Pakistan.

Base URL: `http://localhost:8000/api` (or relative `/api` on deployed domains)

---

## 1. System & Config

### `GET /api/health`
Health check endpoint responding in < 5ms without external dependencies.
- **Response `200`**:
  ```json
  {
    "status": "ok",
    "app_env": "dev",
    "demo_mode": true,
    "ai_demo_mode": true,
    "timestamp": "2026-10-04T05:00:00Z",
    "version": "1.0.0"
  }
  ```

### `GET /api/config`
Public runtime configuration for frontend client. Never exposes secrets or backend API keys.
- **Response `200`**:
  ```json
  {
    "supabase_url": "",
    "supabase_anon_key": "",
    "demo_mode": true,
    "ai_demo_mode": true,
    "public_base_url": "http://localhost:8000",
    "environment": "dev"
  }
  ```

---

## 2. Destinations & Weather

### `GET /api/destinations`
Lists all supported Northern Pakistan destinations.
- **Response `200`**: `List[DestinationSummary]`

### `GET /api/destinations/{slug}`
Retrieves detailed destination profile with live Open-Meteo weather, road status, popular places, and verified businesses.
- **Path Param**: `slug` (e.g. `naran`, `hunza`, `skardu`, `swat`)
- **Response `200`**: `DestinationDetail`

### `GET /api/weather/{slug}`
Fetches real-time weather, high/low temperatures, precipitation risk, and hazard evaluations from Open-Meteo (cached 30 min).
- **Response `200`**: `WeatherForecastResponse`

---

## 3. Places & Spatial Exploration

### `GET /api/places`
Search and filter points of interest.
- **Query Params**:
  - `destination`: Destination slug (e.g. `naran`)
  - `type`: `attraction`, `hotel`, `restaurant`, `fuel`, `hospital`, `atm`
  - `search`: Case-insensitive text query

### `GET /api/places/nearby`
Finds points of interest sorted by ascending Haversine distance from given coordinates.
- **Query Params**:
  - `lat`: float (e.g. `34.9089`)
  - `lng`: float (e.g. `73.6528`)
  - `radius_km`: float (default `25.0`)

---

## 4. AI Trip Planning & Budget

### `POST /api/trips/plan` (SSE Stream)
Generates personalized day-by-day itinerary with verified places, deterministic budget calculation, and road safety warnings.
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "origin": "Islamabad",
    "destination_slug": "naran",
    "duration_days": 3,
    "travelers_count": 4,
    "budget_pkr": 35000,
    "transport_type": "car",
    "interests": ["nature", "adventure"]
  }
  ```
- **Stream Events**:
  - `event: step` (steps 0 to 3 driving frontend loading UI)
  - `event: complete` (emits full `TripResponse` JSON)

### `POST /api/trips/replan`
Dynamically adjusts an existing itinerary if new weather or road hazards are detected.

### `GET /api/trips/{id}/pdf`
Downloads a formatted PDF voucher of the itinerary and budget breakdown generated via ReportLab.

---

## 5. Vision AI & Multimodal Road Reporting

### `POST /api/vision/road`
Uploads a road photo for hazard detection (mud, standing water, snow, landslides).
- **Content-Type**: `multipart/form-data`
- **Form Fields**: `file` (JPEG, PNG, WebP <= 8 MB)
- **Security**: Strips EXIF metadata, verifies magic bytes, re-encodes with Pillow.
- **Response `200`**:
  ```json
  {
    "is_road_photo": true,
    "issues": ["Mud", "Standing Water"],
    "severity": "medium",
    "confidence": 0.88,
    "summary": "Possible mud and water puddles detected on roadway surface.",
    "suggested_status": "caution",
    "disclaimer": "Possible issue detected — AI suggestion, please confirm. Vision results are supporting evidence, not guarantees."
  }
  ```

### `POST /api/vision/identify-place`
Identifies landmarks from visitor photos and provides travel guidance.

### `GET /api/reports`
Lists community road reports with confirm and cleared votes count.

### `POST /api/reports`
Submits a community road report. High-severity reports automatically fan out into travel alerts.

### `POST /api/reports/{id}/vote`
Cast a verification vote (`confirm` or `cleared`).

---

## 6. Grounded Chatbot & Voice Assistant

### `POST /api/chat`
Conversational tourism assistant equipped with tool-calling capabilities. Never invents places; supports English, Urdu, and Roman Urdu.
- **Request Body**:
  ```json
  {
    "message": "What is the weather in Naran?",
    "destination_slug": "naran"
  }
  ```
- **Response `200`**:
  ```json
  {
    "text": "The current weather in Naran is 18°C (Partly Cloudy)...",
    "cards": [
      { "emoji": "🌡️", "title": "18°C", "subtitle": "Partly Cloudy" }
    ]
  }
  ```

### `POST /api/voice/parse`
Parses spoken audio recordings or transcripts into structured trip parameters with Urdu numeral normalization ("40 hazar" -> 40000).

---

## 7. Travel Alerts & Web Push

### `GET /api/alerts`
Lists active travel advisories and authority road closures.

### `GET /api/alerts/stream` (SSE)
Live stream of newly posted alerts with 15-second heartbeat comments.

### `POST /api/internal/cron/weather-alerts`
Protected by `Authorization: Bearer <CRON_SECRET>`. Inspects weather across all destinations and posts advisories if adverse conditions arise.
