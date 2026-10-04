import json
import logging
from typing import Dict, Any, List, Optional
from backend.app.services.weather_rules import evaluate_activity_safety
from backend.app.services.weather import get_destination_weather
from backend.app.db.repositories import DestinationRepo, RoadReportRepo, PlaceRepo
from backend.app.db.sqlite_demo import get_db_connection

logger = logging.getLogger("navigo.services.replanner")

async def replan_trip(trip_id: str, simulated_hazard: Optional[str] = None) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ? OR share_slug = ?", (trip_id, trip_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Trip '{trip_id}' not found.")

    trip_data = dict(row)
    dest_slug = trip_data.get("destination_slug", "naran")
    days = json.loads(trip_data.get("itinerary_json", "[]"))

    dest = DestinationRepo.get_by_slug(dest_slug)
    lat = dest["latitude"] if dest else 34.9089
    lng = dest["longitude"] if dest else 73.6528

    weather = await get_destination_weather(lat, lng)
    if simulated_hazard:
        weather["hazard"] = simulated_hazard
        weather["cond"] = "Heavy Rain"
        weather["precip_probability"] = 80

    reports = RoadReportRepo.get_reports(destination_slug=dest_slug)
    places = PlaceRepo.get_places(destination_slug=dest_slug)

    changes_made = []
    adjusted_days = []

    for day in days:
        new_stops = []
        for stop in day.get("stops", []):
            is_safe, reason, alt = evaluate_activity_safety(
                activity_name=stop.get("activity", ""),
                place_name=stop.get("place_name", ""),
                weather=weather,
                road_reports=reports
            )

            if not is_safe:
                changes_made.append({
                    "day": day.get("day_badge"),
                    "original_place": stop.get("place_name"),
                    "reason": reason,
                    "replacement": alt
                })
                new_stops.append({
                    "place_name": f"{stop.get('place_name')} (Adjusted)",
                    "activity": alt or "Alternative indoor sightseeing & tea",
                    "time_of_day": stop.get("time_of_day", "Afternoon")
                })
            else:
                new_stops.append(stop)

        day_copy = dict(day)
        day_copy["stops"] = new_stops
        adjusted_days.append(day_copy)

    explanation = ""
    if changes_made:
        items_str = "; ".join([f"{c['original_place']} ({c['reason']})" for c in changes_made])
        explanation = f"⚠️ Dynamic Itinerary Adjustment: Weather and road risk detected for {items_str}.naviGo has automatically scheduled safer alternatives."
    else:
        explanation = "✓ Itinerary verified. Current road conditions and weather forecast remain safe for your planned route."

    # Update DB with adjusted itinerary
    if changes_made:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE trips SET itinerary_json = ? WHERE id = ?", (json.dumps(adjusted_days), trip_data["id"]))
        conn.commit()
        conn.close()

    return {
        "trip_id": trip_data["id"],
        "destination_slug": dest_slug,
        "changes_count": len(changes_made),
        "changes": changes_made,
        "explanation": explanation,
        "adjusted_days": adjusted_days
    }
