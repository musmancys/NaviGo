from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ReviewCreateRequest(BaseModel):
    business_id: str
    destination_slug: str = "naran"
    user_name: str
    rating: int = Field(ge=1, le=5)
    comment: str

class ReviewResponse(BaseModel):
    id: str
    business_id: str
    destination_slug: str
    user_name: str
    rating: int
    comment: str
    created_at: str

class ReviewSummaryResponse(BaseModel):
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    based_on_count: int = 0

class BusinessCreateRequest(BaseModel):
    destination_slug: str
    business_type: str = "hotel" # hotel, guide, jeep, restaurant, camping, adventure, handicrafts
    name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    price_range: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    facilities: List[str] = Field(default_factory=list)

class BusinessResponse(BaseModel):
    id: str
    destination_slug: str
    business_type: str
    name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    price_range: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    facilities: List[str] = Field(default_factory=list)
    is_verified: bool = False
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    rating: float = 4.8
    created_at: Optional[str] = None

class BusinessDetailResponse(BusinessResponse):
    reviews: List[ReviewResponse] = Field(default_factory=list)
    ai_summary: Optional[ReviewSummaryResponse] = None
