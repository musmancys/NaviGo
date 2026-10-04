from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TripPlanRequest(BaseModel):
    origin: str = Field(default="Islamabad")
    destination_slug: str = Field(default="naran")
    duration_days: int = Field(default=3, ge=1, le=14)
    travelers_count: int = Field(default=4, ge=1, le=20)
    budget_pkr: int = Field(default=35000, ge=5000)
    transport_type: str = Field(default="car")
    interests: List[str] = Field(default=["nature", "adventure"])

class TripStop(BaseModel):
    place_name: str
    activity: str
    time_of_day: str # Morning, Afternoon, Evening

class DayPlan(BaseModel):
    day_number: int
    day_badge: str
    theme: str
    stops: List[TripStop]
    notes: Optional[str] = None

class TripResponse(BaseModel):
    id: str
    title: str
    destination_slug: str
    origin: str
    duration_days: int
    travelers_count: int
    budget_pkr: int
    transport_type: str
    interests: List[str] = []
    days: List[DayPlan]
    budget_breakdown: Dict[str, Any]
    weather_summary: Optional[Dict[str, Any]] = None
    road_warnings: List[str] = []
    status: str = "draft"
    share_slug: Optional[str] = None
    created_at: Optional[str] = None
