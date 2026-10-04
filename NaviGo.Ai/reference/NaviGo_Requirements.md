# NaviGo — Requirements Specification & Architecture Contract

## 1. Overview & Vision
NaviGo (originating from TourMate AI) is a production-quality, multimodal AI tourism platform designed specifically for Northern Pakistan (Naran, Hunza, Skardu, Swat, Murree, Kashmir, Gilgit, Fairy Meadows, and surrounding valleys).
The platform bridges scattered tourism information (road closures, weather risks, budget realities, verified local guides/hotels) with AI assistance, multimodal road condition reporting, deterministic budgeting, and safety-aware replanning.

## 2. System Architecture & Tech Stack
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+ modular), Leaflet.js with OpenStreetMap tiles, DOMPurify, MediaRecorder & Web Speech API fallback, EventSource (SSE), Service Worker (Web Push). Preserves the original NaviGo design system (Navy `#0B1F33`, Teal `#13B8A6`, Sky `#4DA3FF`, Inter font).
- **Backend**: Python 3.10+ FastAPI (async), Uvicorn, Pydantic v2, HTTPX, Supabase Python Client, Pillow (image validation/EXIF stripping), slowapi (rate limiting), pywebpush (VAPID), ReportLab (PDF itinerary export).
- **Database/Auth/Storage/Realtime**: Supabase (PostgreSQL with PostGIS for spatial queries and pgvector for semantic search/RAG), Supabase Auth (JWT, RBAC: tourist, business, authority, admin), Supabase Storage.
- **Local / Demo Mode**: Zero-dependency offline fallback mode running against seeded SQLite / JSON data with realistic mock AI responses when external API keys or Supabase connections are absent.
- **AI Engine**: Configurable Multi-provider abstraction (`GEMINI_MODEL`, etc.) with Google Gemini API as primary (LLM structured output, Vision multimodal inspection, Audio transcription & parameter extraction, text embeddings) and optional Anthropic Claude fallback with automatic exponential backoff.

## 3. Core Principles & Non-Negotiables
1. **Safety & Honesty in AI**: Vision and road identification outputs are supporting evidence and never guarantees. The system must never claim "road is safe". Road status is labelled as community-reported/unofficial with a "last updated" timestamp. Official authority overrides take precedence.
2. **Deterministic Arithmetic**: LLMs do not calculate budgets or make safety rules. Budgets are computed using deterministic calculation against configurable price tables; weather and road hazards are evaluated by a rule engine. The LLM generates the itinerary structure, narrative, and advice.
3. **Security & Sanitization**: Every user input is strictly validated via Pydantic. DOMPurify is used before any dynamic HTML insertion. Uploads are strictly checked (size <= 8MB, MIME type, magic bytes) and re-encoded using Pillow with EXIF metadata stripped. Rate limits are applied strictly on AI endpoints.
4. **Local & Cloud Parity**: Deployable on Replit (Autoscale/Reserved VM), Render, Railway, Fly.io, and local environments via unified environment configuration (`PORT`, `PUBLIC_BASE_URL`, `APP_ENV`).

## 4. Data Model & Schema (§4)
- **destinations**: `id`, `slug`, `name`, `sub_title`, `about`, `hero_image_url`, `from_price_pkr`, `tags` (array), `best_season`, `latitude`, `longitude`, `created_at`
- **places**: `id`, `destination_id`, `name`, `place_type` (attraction, hotel, restaurant, fuel, hospital, atm, guide), `icon`, `latitude`, `longitude`, `description`, `price_level`, `rating`, `address`, `contact_phone`, `is_verified`, `created_at`
- **trips**: `id`, `user_id`, `destination_id`, `title`, `duration_days`, `travelers_count`, `budget_pkr`, `transport_type`, `interests` (array), `itinerary_json`, `budget_breakdown_json`, `status` (draft, upcoming, completed), `share_slug`, `created_at`, `updated_at`
- **road_reports**: `id`, `user_id`, `destination_id`, `road_name`, `status` (open, caution, closed), `issue_tags` (array), `severity` (low, medium, high, severe), `confidence` (float), `ai_analysis_json`, `photo_url`, `latitude`, `longitude`, `confirmations_count`, `cleared_votes_count`, `is_authority_override`, `created_at`, `expires_at`
- **alerts**: `id`, `destination_id`, `title`, `description`, `alert_type` (road_closure, weather_warning, landslide, flooding, traffic, security), `severity` (info, warning, emergency), `source` (authority, ai_weather_cron, high_confidence_report), `is_active`, `created_at`, `expires_at`
- **businesses**: `id`, `user_id`, `destination_id`, `business_type` (hotel, guide, jeep, restaurant, camping, adventure, handicrafts), `name`, `contact_name`, `phone`, `email`, `description`, `price_range`, `photos` (array), `facilities` (array), `is_verified`, `verified_at`, `verified_by`, `rating`, `created_at`
- **reviews**: `id`, `business_id`, `destination_id`, `user_id`, `rating`, `comment`, `created_at`
- **review_summaries**: `id`, `business_id`, `destination_id`, `summary_type`, `pros` (array), `cons` (array), `review_count`, `updated_at`
- **price_catalog**: `id`, `item_key`, `category`, `base_price_pkr`, `unit`, `notes`, `updated_at`
- **profiles**: `id`, `user_id`, `full_name`, `role` (tourist, business, authority, admin), `preferred_language` (en, ur), `created_at`

## 5. Feature Requirements (§5)
1. **AI Trip Planner**: Accepts origin, destination, duration, travelers, budget, interests, and transport. Gathers context (places, live weather forecast via Open-Meteo, road reports, price table). Emits SSE events driving the 4-step frontend animation, returns structured itinerary + deterministic budget + hazard warnings.
2. **Weather- & Road-Aware Replanning**: Rules engine monitors weather and road conditions. Allows automated or manual re-routing and activity swapping.
3. **Smart Tourism Map**: Leaflet.js interactive map replacing fake CSS pins. Filter by category, marker clustering, popups with direct action, layer controls, and "What's Around Me?" geolocation with emergency numbers.
4. **Live Road Conditions & Photo Reporter (Multimodal Hero)**: Upload road photo, analyze with Vision AI (detect mud, snow, landslide, standing water, blockage with confidence, severity, and safety disclaimer). Map pin placement via EXIF/GPS/click. Voting model (confirm / still-there / cleared) and authority verification.
5. **Urdu / Roman Urdu / English Voice Assistant**: Accepts audio recordings (WebM/WAV) or Web Speech fallback. Extracts destination, duration, budget ("40 hazar" -> 40000), travelers, and interests.
6. **Grounded Tourism Chatbot with Tool Calling**: Tool-calling agent (`get_weather`, `get_road_status`, `search_places`, `search_businesses`, `get_trip`, `estimate_budget`, `nearby`). SSE streaming response, rendering rich cards. Cites facts, never invents places.
7. **Local Marketplace & Verified Profiles**: Listings for hotels, local guides, jeeps, adventure operators. Formal admin verification timestamp ("Verified Business · Last verified: September 2026").
8. **Reviews with AI Summaries**: Auto-generated pros & cons summaries from real tourist reviews.
9. **Identify This Place**: Multimodal landmark identification constrained to Northern Pakistan catalog with confidence score and nearby recommendations.
10. **Alerts Centre & Web Push**: Real-time alerts via SSE toasts and Web Push notifications. Automated 30-min weather check cron.
11. **Profile, Settings, & Urdu RTL Localization**: Language switcher (English / Urdu with right-to-left layout), custom units, saved destinations, and user reports history.
12. **PDF Export & Share Links**: Export trip itinerary to PDF via ReportLab; public shareable trip link.

## 6. API Contract (§6)
- `GET /api/config` -> `{ supabase_url, supabase_anon_key, demo_mode, environment, version }`
- `GET /api/health` -> `{ status: "ok", demo_mode: bool, timestamp }`
- `GET /api/destinations` -> `List[Destination]`
- `GET /api/destinations/{slug}` -> `DestinationDetail` (includes live weather, active road reports, popular places, verified businesses)
- `GET /api/weather/{slug}` -> `WeatherForecast` (current, hourly, 7-day, risk score)
- `GET /api/places` -> `List[Place]` (filters: destination, type, bbox, query)
- `GET /api/places/nearby` -> `List[Place]` (lat, lng, radius_km, types)
- `POST /api/trips/plan` -> SSE stream: `{ step: 1..4, message: str }` -> `{ trip: TripResponse }`
- `POST /api/trips/replan` -> `{ trip_id, changes, explanation, warnings }`
- `GET /api/trips` -> `List[TripSummary]` (current user or session)
- `GET /api/trips/{id}` -> `TripResponse`
- `PUT /api/trips/{id}` -> `TripResponse`
- `DELETE /api/trips/{id}` -> `{ success: true }`
- `GET /api/trips/{id}/pdf` -> `application/pdf`
- `GET /api/trips/share/{slug}` -> `TripResponse` (public read)
- `POST /api/budget/calculate` -> `BudgetBreakdown` (deterministic)
- `POST /api/chat` -> SSE stream: text chunks, markdown, card components
- `POST /api/voice/parse` -> `{ transcript, language, params: { origin, destination, duration_days, budget_pkr, travelers, interests }, missing_fields }`
- `POST /api/vision/road` -> `{ is_road_photo, issues: [], severity, confidence, summary, suggested_status, disclaimer }`
- `POST /api/vision/identify-place` -> `{ matches: [{ place_name, confidence, description, nearby_places }], disclaimer }`
- `GET /api/reports` -> `List[RoadReport]`
- `POST /api/reports` -> `RoadReport` (creates report, updates map, fans out alert if high severity)
- `POST /api/reports/{id}/vote` -> `{ id, confirmations, cleared_votes, status }`
- `GET /api/alerts` -> `List[Alert]` (active alerts)
- `GET /api/alerts/stream` -> SSE stream for live alerts
- `POST /api/alerts` -> `Alert` (authority / admin only)
- `GET /api/businesses` -> `List[Business]` (filters: destination, type, verified_only)
- `GET /api/businesses/{id}` -> `BusinessDetail` (includes reviews and AI review summary)
- `POST /api/businesses` -> `Business` (partner registration)
- `POST /api/reviews` -> `Review`
- `GET /api/me/profile` -> `UserProfile`
- `PUT /api/me/profile` -> `UserProfile`
- `GET /api/me/saved` -> `List[Destination]`
- `POST /api/me/saved/{slug}` -> toggle saved destination
- `POST /api/internal/cron/weather-alerts` -> `{ checked: int, alerts_generated: int }` (protected by `CRON_SECRET`)

## 7. Acceptance Criteria & Definition of Done
1. `./scripts/run_local.sh` or `run_local.ps1` boots the platform cleanly.
2. `scripts/smoke_test.py` validates the complete critical path against `http://localhost:8000` or deployed URL.
3. Every page in the frontend is interactive and dynamic with no mock static stubs or toast-only actions.
4. Seamless fallback into Demo Mode if no Supabase or AI keys are provided, with zero crashes and clear demo indicator badge.
5. All tests in `tests/` pass with pytest.
6. Documentation includes `README.md`, `API.md`, `docs/DEPLOY_REPLIT.md`, and `docs/DEMO_SCRIPT.md`.
