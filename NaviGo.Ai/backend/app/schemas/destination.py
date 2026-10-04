from typing import List, Optional, Any
from pydantic import BaseModel, Field
from backend.app.schemas.weather import WeatherForecastResponse

class PlaceSummary(BaseModel):
    id: str
    name: str
    place_type: str
    icon: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    price_level: Optional[str] = None
    rating: Optional[float] = 4.5

class BusinessSummary(BaseModel):
    id: str
    name: str
    business_type: str
    phone: Optional[str] = None
    price_range: Optional[str] = None
    facilities: List[str] = []
    is_verified: bool = False
    verified_at: Optional[str] = None
    rating: float = 4.8

class DestinationSummary(BaseModel):
    id: str
    slug: str
    name: str
    sub_title: Optional[str] = None
    about: Optional[str] = None
    hero_image_url: Optional[str] = None
    from_price_pkr: int = 0
    tags: List[str] = []
    best_season: Optional[str] = None
    latitude: float
    longitude: float

class DestinationDetail(DestinationSummary):
    weather: Optional[WeatherForecastResponse] = None
    road_status: str = "Open"
    road_updated: str = "10 minutes ago"
    popular_places: List[PlaceSummary] = []
    verified_businesses: List[BusinessSummary] = []
    active_alerts: List[Any] = []
