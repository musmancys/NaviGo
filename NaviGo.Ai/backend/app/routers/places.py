import math
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from backend.app.db.repositories import PlaceRepo

router = APIRouter(prefix="/places", tags=["Places"])

class PlaceResponse(BaseModel):
    id: str
    destination_slug: str
    name: str
    place_type: str
    icon: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    price_level: Optional[str] = None
    rating: Optional[float] = 4.5
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    is_verified: bool = False
    distance_km: Optional[float] = None

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

@router.get("", response_model=List[PlaceResponse])
async def list_places(
    destination: Optional[str] = Query(None, description="Filter by destination slug (e.g. naran, hunza)"),
    type: Optional[str] = Query(None, description="Filter by place type (attraction, hotel, restaurant, fuel, hospital, atm)"),
    search: Optional[str] = Query(None, description="Text search on place name or description")
):
    places = PlaceRepo.get_places(destination_slug=destination, place_type=type, search=search)
    return [
        PlaceResponse(
            id=p["id"],
            destination_slug=p["destination_slug"],
            name=p["name"],
            place_type=p["place_type"],
            icon=p.get("icon", "📍"),
            latitude=p["latitude"],
            longitude=p["longitude"],
            description=p.get("description"),
            price_level=p.get("price_level"),
            rating=p.get("rating", 4.5),
            address=p.get("address"),
            contact_phone=p.get("contact_phone"),
            is_verified=bool(p.get("is_verified", 0))
        )
        for p in places
    ]

@router.get("/nearby", response_model=List[PlaceResponse])
async def get_nearby_places(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(25.0, description="Search radius in kilometers"),
    type: Optional[str] = Query(None, description="Optional category filter")
):
    all_places = PlaceRepo.get_places(place_type=type)
    nearby = []

    for p in all_places:
        dist = haversine_km(lat, lng, p["latitude"], p["longitude"])
        if dist <= radius_km:
            place_obj = PlaceResponse(
                id=p["id"],
                destination_slug=p["destination_slug"],
                name=p["name"],
                place_type=p["place_type"],
                icon=p.get("icon", "📍"),
                latitude=p["latitude"],
                longitude=p["longitude"],
                description=p.get("description"),
                price_level=p.get("price_level"),
                rating=p.get("rating", 4.5),
                address=p.get("address"),
                contact_phone=p.get("contact_phone"),
                is_verified=bool(p.get("is_verified", 0)),
                distance_km=dist
            )
            nearby.append(place_obj)

    # Sort ascending by distance
    nearby.sort(key=lambda x: x.distance_km if x.distance_km is not None else 99999)
    return nearby
