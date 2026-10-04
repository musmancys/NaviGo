from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RoadAnalysisResponse(BaseModel):
    is_road_photo: bool = True
    issues: List[str] = Field(default_factory=list)
    severity: str = "medium" # low, medium, high, severe
    confidence: float = 0.85
    summary: str
    suggested_status: str = "caution" # open, caution, closed
    disclaimer: str

class CreateReportRequest(BaseModel):
    destination_slug: str = "naran"
    road_name: str
    status: str = "caution"
    issue_tags: List[str] = Field(default_factory=list)
    severity: str = "medium"
    confidence: float = 0.85
    summary: Optional[str] = None
    photo_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class VoteReportRequest(BaseModel):
    vote_type: str = "confirm" # confirm or cleared

class RoadReportResponse(BaseModel):
    id: str
    destination_slug: str
    road_name: str
    status: str
    issue_tags: List[str] = Field(default_factory=list)
    severity: str
    confidence: float
    summary: Optional[str] = None
    photo_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confirmations_count: int = 0
    cleared_votes_count: int = 0
    is_authority_override: bool = False
    created_at: str
    time_ago: Optional[str] = "Recently reported"
