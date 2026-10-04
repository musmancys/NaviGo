import json
import uuid
import logging
from typing import Dict, Any, List
from backend.app.config import settings
from backend.app.schemas.trip import TripPlanRequest, TripResponse, DayPlan, TripStop
from backend.app.db.repositories import DestinationRepo, PlaceRepo, RoadReportRepo, AlertRepo
from backend.app.services.weather import get_destination_weather
from backend.app.services.budget import calculate_trip_budget

logger = logging.getLogger("navigo.services.planner")

async def plan_trip_pipeline(req: TripPlanRequest) -> TripResponse:
    dest = DestinationRepo.get_by_slug(req.destination_slug)
    dest_name = dest["name"] if dest else req.destination_slug.title()

    # 1. Gather Context
    places = PlaceRepo.get_places(destination_slug=req.destination_slug)
    reports = RoadReportRepo.get_reports(destination_slug=req.destination_slug)
    alerts = AlertRepo.get_active(destination_slug=req.destination_slug)
    weather = await get_destination_weather(
        dest["latitude"] if dest else 34.9089,
        dest["longitude"] if dest else 73.6528
    )

    # 2. Safety & Road Warnings from context
    warnings = []
    if weather.get("hazard"):
        warnings.append(weather["hazard"])
    for a in alerts:
        warnings.append(f"Alert: {a['title']} — {a['description']}")
    for r in reports:
        if r.get("status") in ["caution", "closed"]:
            warnings.append(f"Road notice: {r['road_name']} is currently marked as {r['status'].upper()}.")

    # 3. Deterministic Budget
    budget_breakdown = calculate_trip_budget(
        duration_days=req.duration_days,
        travelers_count=req.travelers_count,
        target_budget_pkr=req.budget_pkr,
        transport_type=req.transport_type
    )

    # 4. Generate Itinerary (Gemini if key present, else OpenAI/ChatGPT if key present, otherwise deterministic generator)
    days = []
    if settings.gemini_api_key and not settings.is_ai_demo_mode:
        try:
            days = await call_gemini_planner(req, dest_name, places, weather, warnings)
        except Exception as e:
            logger.warning("Gemini AI planning failed (%s). Checking OpenAI/ChatGPT fallback.", e)
            if settings.effective_openai_api_key:
                try:
                    from backend.app.services.llm.openai import call_openai_planner
                    days = await call_openai_planner(req, dest_name, places, weather, warnings)
                except Exception as oe:
                    logger.warning("OpenAI planning failed (%s). Falling back to rule-based planner.", oe)
                    days = generate_rule_based_itinerary(req, dest_name, places)
            else:
                days = generate_rule_based_itinerary(req, dest_name, places)
    elif settings.effective_openai_api_key:
        try:
            from backend.app.services.llm.openai import call_openai_planner
            days = await call_openai_planner(req, dest_name, places, weather, warnings)
        except Exception as e:
            logger.warning("OpenAI planning failed (%s). Falling back to rule-based planner.", e)
            days = generate_rule_based_itinerary(req, dest_name, places)
    else:
        days = generate_rule_based_itinerary(req, dest_name, places)

    trip_id = f"trip-{uuid.uuid4().hex[:8]}"
    share_slug = f"{req.destination_slug}-{uuid.uuid4().hex[:6]}"

    return TripResponse(
        id=trip_id,
        title=f"Your {dest_name} Adventure",
        destination_slug=req.destination_slug,
        origin=req.origin,
        duration_days=req.duration_days,
        travelers_count=req.travelers_count,
        budget_pkr=req.budget_pkr,
        transport_type=req.transport_type,
        interests=req.interests,
        days=days,
        budget_breakdown=budget_breakdown,
        weather_summary=weather,
        road_warnings=warnings,
        status="draft",
        share_slug=share_slug
    )

async def call_gemini_planner(req: TripPlanRequest, dest_name: str, places: List[Dict[str, Any]], weather: Dict[str, Any], warnings: List[str]) -> List[DayPlan]:
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"

    places_str = "\n".join([f"- {p['name']} ({p['place_type']}): {p.get('description', '')}" for p in places[:15]])
    warnings_str = "\n".join([f"- {w}" for w in warnings]) if warnings else "None"

    prompt = f"""
You are NaviGo's expert Pakistan travel planning AI.
Create a realistic {req.duration_days}-day itinerary for {dest_name}, starting from {req.origin}.
Travelers: {req.travelers_count}, Interests: {', '.join(req.interests)}, Transport: {req.transport_type}.

Current Weather: {weather.get('temp')}°C, {weather.get('cond')}.
Safety & Travel Alerts:
{warnings_str}

VERIFIED PLACES IN DATABASE (prioritize these if they exist for this destination):
{places_str if places_str else "No pre-seeded places for this destination — use your knowledge of real, verified places in " + dest_name + ", Pakistan."}

IMPORTANT RULES:
1. If verified places are listed above, you MUST use those names exactly.
2. If no verified places exist (empty list), use your knowledge to suggest real, well-known attractions, hotels, and restaurants in {dest_name}.
3. For city destinations (Lahore, Karachi, Islamabad, Peshawar, Multan etc.), include iconic landmarks, food streets, museums, and cultural sites.
4. For coastal destinations (Gwadar, Ormara), include beaches, fishing villages, and port attractions.
5. For heritage sites (Mohenjo-daro, Taxila, Makli), focus on archaeological and historical significance.
6. Always include practical stops: a good local restaurant, hotel check-in, and any safety notes relevant to the region.

Respond STRICTLY with valid JSON following this format:
[
  {{
    "day_number": 1,
    "day_badge": "DAY 01",
    "theme": "Arrival & First Impressions",
    "stops": [
      {{ "place_name": "Local Landmark", "activity": "Sightseeing and photography", "time_of_day": "Morning" }}
    ],
    "notes": "Travel tip relevant to this destination and season"
  }}
]
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4
        }
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            res_json = resp.json()
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)
            return [DayPlan(**d) for d in parsed]
        else:
            raise Exception(f"Gemini API returned status {resp.status_code}")

def generate_rule_based_itinerary(req: TripPlanRequest, dest_name: str, places: List[Dict[str, Any]]) -> List[DayPlan]:
    attractions = [p["name"] for p in places if p.get("place_type") == "attraction"]
    hotels = [p["name"] for p in places if p.get("place_type") == "hotel"]
    restaurants = [p["name"] for p in places if p.get("place_type") == "restaurant"]

    hotel_name = hotels[0] if hotels else f"{dest_name} Tourist Guest House"
    dining_spot = restaurants[0] if restaurants else f"Local {dest_name} Restaurant"

    days = []
    for day in range(1, req.duration_days + 1):
        stops = []
        theme = f"Explore {dest_name} Valley"
        badge = f"DAY {day:02d}"

        if day == 1:
            theme = f"Journey from {req.origin} & Local Discovery"
            stops.append(TripStop(place_name=f"Departure from {req.origin}", activity="Scenic drive via Motorway and mountain highway", time_of_day="Morning"))
            stops.append(TripStop(place_name=attractions[0] if attractions else f"{dest_name} Bazaar", activity="First-sight sightseeing & photography", time_of_day="Afternoon"))
            stops.append(TripStop(place_name=hotel_name, activity="Check-in and hot tea", time_of_day="Evening"))
            stops.append(TripStop(place_name=dining_spot, activity="Traditional trout fish and local dinner", time_of_day="Night"))
        elif day == req.duration_days:
            theme = f"Souvenir Shopping & Return Journey"
            if len(attractions) > 1:
                stops.append(TripStop(place_name=attractions[1], activity="Morning reflection and nature walk", time_of_day="Morning"))
            stops.append(TripStop(place_name=f"{dest_name} Main Bazaar", activity="Local handicrafts & dry fruits shopping", time_of_day="Afternoon"))
            stops.append(TripStop(place_name=f"Safe return to {req.origin}", activity="Departure before nightfall", time_of_day="Evening"))
        else:
            attract_idx = (day - 1) % len(attractions) if attractions else 0
            curr_attraction = attractions[attract_idx] if attractions else f"{dest_name} Viewpoint"
            theme = f"Excursion to {curr_attraction}"
            stops.append(TripStop(place_name=curr_attraction, activity="Adventure trekking and exploration", time_of_day="Morning"))
            stops.append(TripStop(place_name=f"{curr_attraction} Surroundings", activity="Boating, photography, and alpine picnic", time_of_day="Afternoon"))
            stops.append(TripStop(place_name=hotel_name, activity="Bonfire and relaxation", time_of_day="Evening"))

        days.append(DayPlan(
            day_number=day,
            day_badge=badge,
            theme=theme,
            stops=stops,
            notes="Carry warm jacket, stay hydrated, and verify road clearance before starting early."
        ))

    return days
