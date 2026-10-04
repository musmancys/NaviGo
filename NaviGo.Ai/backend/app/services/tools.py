import logging
from typing import Dict, Any, List, Optional
from backend.app.db.repositories import DestinationRepo, PlaceRepo, BusinessRepo, RoadReportRepo, AlertRepo
from backend.app.services.weather import get_destination_weather
from backend.app.services.budget import calculate_trip_budget

logger = logging.getLogger("navigo.services.tools")

async def tool_get_weather(destination_slug: str) -> Dict[str, Any]:
    dest = DestinationRepo.get_by_slug(destination_slug)
    if not dest:
        return {"error": f"Destination '{destination_slug}' not found."}
    w = await get_destination_weather(dest["latitude"], dest["longitude"])
    return {
        "destination": dest["name"],
        "temp_c": w["temp"],
        "condition": w["cond"],
        "high_c": w["high"],
        "low_c": w["low"],
        "hazard": w.get("hazard"),
        "wind_kmh": w["wind_kmh"]
    }

async def tool_get_road_status(destination_slug: str) -> Dict[str, Any]:
    reports = RoadReportRepo.get_reports(destination_slug=destination_slug)
    alerts = AlertRepo.get_active(destination_slug=destination_slug)
    status = "Open"
    if reports:
        status = reports[0].get("status", "Open").title()

    return {
        "destination": destination_slug.title(),
        "status": status,
        "recent_reports_count": len(reports),
        "latest_reports": [
            {"road": r["road_name"], "status": r["status"], "issues": r.get("issue_tags", [])}
            for r in reports[:3]
        ],
        "active_alerts": [a["title"] for a in alerts]
    }

async def tool_search_places(destination_slug: str, query: Optional[str] = None, place_type: Optional[str] = None) -> List[Dict[str, Any]]:
    places = PlaceRepo.get_places(destination_slug=destination_slug, place_type=place_type, search=query)
    return [
        {
            "name": p["name"],
            "type": p["place_type"],
            "rating": p.get("rating", 4.5),
            "description": p.get("description", ""),
            "price_level": p.get("price_level", "")
        }
        for p in places[:6]
    ]

async def tool_search_businesses(destination_slug: str, business_type: Optional[str] = None) -> List[Dict[str, Any]]:
    biz = BusinessRepo.get_businesses(destination_slug=destination_slug, business_type=business_type)
    return [
        {
            "name": b["name"],
            "type": b["business_type"],
            "is_verified": bool(b.get("is_verified")),
            "verified_at": b.get("verified_at"),
            "price_range": b.get("price_range"),
            "phone": b.get("phone")
        }
        for b in biz[:5]
    ]

def tool_estimate_budget(duration_days: int, travelers: int, transport: str = "car") -> Dict[str, Any]:
    return calculate_trip_budget(
        duration_days=duration_days,
        travelers_count=travelers,
        target_budget_pkr=35000,
        transport_type=transport
    )

TOOL_DEFINITIONS = [
    {
        "name": "get_weather",
        "description": "Fetch real-time weather, temperature, and hazards for any Pakistan destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_slug": {"type": "string", "description": "e.g. naran, hunza, skardu, swat, murree, lahore, karachi, islamabad, gwadar, quetta"}
            },
            "required": ["destination_slug"]
        }
    },
    {
        "name": "get_road_status",
        "description": "Get current verified and community-reported road conditions and travel alerts for any Pakistan route.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_slug": {"type": "string", "description": "e.g. naran, hunza, skardu, lahore, karachi"}
            },
            "required": ["destination_slug"]
        }
    },
    {
        "name": "search_places",
        "description": "Search tourist attractions, historical sites, viewpoints, hotels, restaurants, or fuel/emergency points anywhere in Pakistan.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_slug": {"type": "string"},
                "query": {"type": "string"}
            },
            "required": ["destination_slug"]
        }
    }
]
