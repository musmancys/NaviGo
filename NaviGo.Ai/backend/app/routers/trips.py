import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.app.schemas.trip import TripPlanRequest, TripResponse
from backend.app.services.planner import plan_trip_pipeline
from backend.app.services.budget import calculate_trip_budget
from backend.app.services.pdf_export import generate_trip_pdf
from backend.app.services.replanner import replan_trip
from backend.app.db.sqlite_demo import get_db_connection

router = APIRouter(prefix="/trips", tags=["Trips"])

# In-memory trip store cache for active session
_ACTIVE_TRIPS: Dict[str, TripResponse] = {}

@router.post("/budget/calculate")
async def calculate_budget_endpoint(
    duration_days: int = 3,
    travelers_count: int = 4,
    budget_pkr: int = 35000,
    transport_type: str = "car",
    hotel_tier: str = "standard"
):
    return calculate_trip_budget(duration_days, travelers_count, budget_pkr, transport_type, hotel_tier)

@router.post("/replan")
async def replan_trip_endpoint(trip_id: str, simulated_hazard: Optional[str] = None):
    try:
        return await replan_trip(trip_id, simulated_hazard)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/plan")
async def plan_trip_sse(req: TripPlanRequest):
    """
    SSE stream emitting the 4 loading steps and returning the completed trip plan.
    """
    async def event_generator():
        # Step 1: Understanding preferences
        yield f"event: step\ndata: {json.dumps({'step': 0, 'message': 'Understanding your preferences'})}\n\n"
        await asyncio.sleep(0.4)

        # Step 2: Selecting destinations & places
        yield f"event: step\ndata: {json.dumps({'step': 1, 'message': f'Selecting destinations in {req.destination_slug.title()}'})}\n\n"
        await asyncio.sleep(0.4)

        # Step 3: Checking weather & road safety
        yield f"event: step\ndata: {json.dumps({'step': 2, 'message': 'Checking live weather and road hazards'})}\n\n"
        await asyncio.sleep(0.4)

        # Step 4: Generating itinerary & budget
        yield f"event: step\ndata: {json.dumps({'step': 3, 'message': 'Preparing your personalized plan'})}\n\n"
        
        trip = await plan_trip_pipeline(req)
        _ACTIVE_TRIPS[trip.id] = trip
        if trip.share_slug:
            _ACTIVE_TRIPS[trip.share_slug] = trip

        # Save to SQLite database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO trips (id, user_id, destination_slug, title, duration_days, travelers_count, budget_pkr, transport_type, interests, itinerary_json, budget_breakdown_json, status, share_slug, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                trip.id, "demo-user-1", trip.destination_slug, trip.title,
                trip.duration_days, trip.travelers_count, trip.budget_pkr,
                trip.transport_type, json.dumps(trip.interests),
                json.dumps([d.model_dump() for d in trip.days]),
                json.dumps(trip.budget_breakdown), trip.status, trip.share_slug
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            pass

        # Final Event
        yield f"event: complete\ndata: {json.dumps(trip.model_dump())}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

DESTINATION_IMAGES = {
    # Northern
    "naran":   "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80",
    "hunza":   "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=400&q=80",
    "skardu":  "https://images.unsplash.com/photo-1509316785289-025f5b846b35?auto=format&fit=crop&w=400&q=80",
    "kashmir": "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=400&q=80",
    "swat":    "https://images.unsplash.com/photo-1533130061792-64b345e4a833?auto=format&fit=crop&w=400&q=80",
    "fairy":   "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80",
    "fairy-meadows": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80",
    "gilgit":  "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=400&q=80",
    "murree":  "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=400&q=80",
    # Cities
    "lahore":    "https://images.unsplash.com/photo-1597040663342-45b6af3d91a5?auto=format&fit=crop&w=400&q=80",
    "karachi":   "https://images.unsplash.com/photo-1567168544813-cc03465b4fa8?auto=format&fit=crop&w=400&q=80",
    "islamabad": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?auto=format&fit=crop&w=400&q=80",
    "peshawar":  "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=400&q=80",
    "quetta":    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=400&q=80",
    "multan":    "https://images.unsplash.com/photo-1559827291-72ee739d0d9a?auto=format&fit=crop&w=400&q=80",
    # Coastal & Heritage
    "gwadar":   "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=400&q=80",
    "taxila":   "https://images.unsplash.com/photo-1591020547040-e8d4e6a59bd7?auto=format&fit=crop&w=400&q=80",
}

SHOWCASE_TRIPS_FALLBACK = [
    {
        "id": "trip-showcase-1",
        "title": "Naran Adventure",
        "destination_slug": "naran",
        "duration_days": 3,
        "travelers_count": 4,
        "budget_pkr": 35000,
        "status": "completed",
        "img": DESTINATION_IMAGES["naran"]
    },
    {
        "id": "trip-showcase-2",
        "title": "Hunza Explorer",
        "destination_slug": "hunza",
        "duration_days": 5,
        "travelers_count": 2,
        "budget_pkr": 60000,
        "status": "completed",
        "img": DESTINATION_IMAGES["hunza"]
    },
    {
        "id": "trip-showcase-3",
        "title": "Skardu Expedition",
        "destination_slug": "skardu",
        "duration_days": 7,
        "travelers_count": 6,
        "budget_pkr": 95000,
        "status": "upcoming",
        "img": DESTINATION_IMAGES["skardu"]
    },
    {
        "id": "trip-showcase-4",
        "title": "Kashmir Dreams",
        "destination_slug": "kashmir",
        "duration_days": 10,
        "travelers_count": 4,
        "budget_pkr": 80000,
        "status": "draft",
        "img": DESTINATION_IMAGES["kashmir"]
    },
    {
        "id": "trip-showcase-5",
        "title": "Weekend in Swat",
        "destination_slug": "swat",
        "duration_days": 2,
        "travelers_count": 3,
        "budget_pkr": 25000,
        "status": "completed",
        "img": DESTINATION_IMAGES["swat"]
    },
    {
        "id": "trip-showcase-6",
        "title": "Fairy Meadows Camp",
        "destination_slug": "fairy-meadows",
        "duration_days": 14,
        "travelers_count": 5,
        "budget_pkr": 110000,
        "status": "draft",
        "img": DESTINATION_IMAGES["fairy-meadows"]
    }
]

@router.get("", response_model=List[Dict[str, Any]])
async def list_trips():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]

    if not rows:
        cursor.execute("SELECT COUNT(*) FROM destinations")
        dest_count = cursor.fetchone()[0]
        conn.close()
        if dest_count > 0:
            return []
        return SHOWCASE_TRIPS_FALLBACK

    conn.close()

    for r in rows:
        slug = r.get("destination_slug", "naran")
        if not r.get("img"):
            r["img"] = DESTINATION_IMAGES.get(slug, DESTINATION_IMAGES["naran"])
        if isinstance(r.get("itinerary_json"), str):
            try:
                r["days"] = json.loads(r["itinerary_json"])
            except Exception:
                r["days"] = []
    return rows

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str):
    if trip_id in _ACTIVE_TRIPS:
        return _ACTIVE_TRIPS[trip_id]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ? OR share_slug = ?", (trip_id, trip_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Trip not found")

    d = dict(row)
    days_data = json.loads(d["itinerary_json"]) if d.get("itinerary_json") else []
    days = []
    for day in days_data:
        if isinstance(day, dict):
            stops = []
            for s in day.get("stops", day.get("places", [])):
                if isinstance(s, dict):
                    stops.append({
                        "place_name": s.get("place_name", s.get("name", "Scenic Spot")),
                        "activity": s.get("activity", s.get("notes", "Sightseeing")),
                        "time_of_day": s.get("time_of_day", s.get("time", "Morning"))
                    })
            days.append({
                "day_number": day.get("day_number", 1),
                "day_badge": day.get("day_badge", f"Day {day.get('day_number', 1)}"),
                "theme": day.get("theme", day.get("title", "Exploration")),
                "stops": stops,
                "notes": day.get("notes", "")
            })

    budget_breakdown = json.loads(d["budget_breakdown_json"]) if d.get("budget_breakdown_json") else {}

    return TripResponse(
        id=d["id"],
        title=d["title"],
        destination_slug=d["destination_slug"],
        origin="Islamabad",
        duration_days=d["duration_days"],
        travelers_count=d["travelers_count"],
        budget_pkr=d["budget_pkr"],
        transport_type=d["transport_type"],
        interests=json.loads(d["interests"]) if d.get("interests") else [],
        days=days,
        budget_breakdown=budget_breakdown,
        status=d.get("status", "draft"),
        share_slug=d.get("share_slug")
    )

@router.delete("/{trip_id}")
async def delete_trip(trip_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()
    if trip_id in _ACTIVE_TRIPS:
        del _ACTIVE_TRIPS[trip_id]
    return {"success": True, "message": "Trip deleted"}

@router.get("/{trip_id}/pdf")
async def export_trip_pdf(trip_id: str):
    trip = await get_trip(trip_id)
    pdf_bytes = generate_trip_pdf(trip)
    filename = f"NaviGo_Trip_{trip.destination_slug.title()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/share/{slug}", response_model=TripResponse)
async def get_shared_trip(slug: str):
    return await get_trip(slug)
