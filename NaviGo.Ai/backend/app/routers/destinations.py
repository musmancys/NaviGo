from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.destination import DestinationSummary, DestinationDetail, PlaceSummary, BusinessSummary
from backend.app.db.repositories import DestinationRepo, PlaceRepo, BusinessRepo, RoadReportRepo, AlertRepo
from backend.app.services.weather import get_destination_weather

router = APIRouter(prefix="/destinations", tags=["Destinations"])

@router.get("", response_model=List[DestinationSummary])
async def list_destinations():
    destinations = DestinationRepo.get_all()
    return destinations

@router.get("/{slug}", response_model=DestinationDetail)
async def get_destination_detail(slug: str):
    dest = DestinationRepo.get_by_slug(slug)
    if not dest:
        raise HTTPException(status_code=404, detail=f"Destination '{slug}' not found")

    # Fetch live weather via Open-Meteo
    weather_data = await get_destination_weather(dest["latitude"], dest["longitude"])

    # Fetch places, businesses, reports, alerts
    places = PlaceRepo.get_places(destination_slug=slug)
    businesses = BusinessRepo.get_businesses(destination_slug=slug)
    reports = RoadReportRepo.get_reports(destination_slug=slug)
    alerts = AlertRepo.get_active(destination_slug=slug)

    # Determine aggregated road status
    road_status = "Open"
    road_updated = "10 minutes ago"
    if reports:
        latest = reports[0]
        road_status = latest.get("status", "Open").title()
        road_updated = "Recently reported by community"

    popular_places = [
        PlaceSummary(
            id=p["id"],
            name=p["name"],
            place_type=p["place_type"],
            icon=p.get("icon", "📍"),
            latitude=p["latitude"],
            longitude=p["longitude"],
            description=p.get("description"),
            price_level=p.get("price_level"),
            rating=p.get("rating", 4.5)
        )
        for p in places[:6]
    ]

    verified_businesses = [
        BusinessSummary(
            id=b["id"],
            name=b["name"],
            business_type=b["business_type"],
            phone=b.get("phone"),
            price_range=b.get("price_range"),
            facilities=b.get("facilities", []),
            is_verified=bool(b.get("is_verified")),
            verified_at=b.get("verified_at"),
            rating=b.get("rating", 4.8)
        )
        for b in businesses
    ]

    return DestinationDetail(
        **dest,
        weather=weather_data,
        road_status=road_status,
        road_updated=road_updated,
        popular_places=popular_places,
        verified_businesses=verified_businesses,
        active_alerts=alerts
    )
