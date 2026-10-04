import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.app.db.sqlite_demo import get_db_connection
from backend.app.db.repositories import DestinationRepo, RoadReportRepo

router = APIRouter(prefix="/me", tags=["User Profile"])

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = "en"

class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    role: str
    preferred_language: str
    saved_destinations: List[str] = []

@router.get("", response_model=UserProfileResponse)
@router.get("/profile", response_model=UserProfileResponse)
async def get_my_profile():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE user_id = 'demo-user-1'")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return UserProfileResponse(
            id="prof-1",
            user_id="demo-user-1",
            full_name="Traveler",
            email="traveler@navigo.pk",
            role="tourist",
            preferred_language="en",
            saved_destinations=["naran", "hunza"]
        )

    d = dict(row)
    saved = json.loads(d["saved_destinations"]) if d.get("saved_destinations") else []
    return UserProfileResponse(
        id=d["id"],
        user_id=d["user_id"],
        full_name=d.get("full_name") or "Traveler",
        email=d.get("email") or "traveler@navigo.pk",
        role=d.get("role", "tourist"),
        preferred_language=d.get("preferred_language", "en"),
        saved_destinations=saved
    )

@router.put("/profile", response_model=UserProfileResponse)
async def update_my_profile(req: UpdateProfileRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    if req.full_name:
        cursor.execute("UPDATE profiles SET full_name = ? WHERE user_id = 'demo-user-1'", (req.full_name,))
    if req.preferred_language:
        cursor.execute("UPDATE profiles SET preferred_language = ? WHERE user_id = 'demo-user-1'", (req.preferred_language,))

    conn.commit()
    conn.close()
    return await get_my_profile()

@router.get("/saved")
async def get_saved_destinations():
    profile = await get_my_profile()
    all_dest = DestinationRepo.get_all()
    saved = [d for d in all_dest if d["slug"] in profile.saved_destinations]
    return saved

@router.post("/saved/{slug}")
async def toggle_save_destination(slug: str):
    profile = await get_my_profile()
    saved = list(profile.saved_destinations)

    if slug in saved:
        saved.remove(slug)
        action = "removed"
    else:
        saved.append(slug)
        action = "saved"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE profiles SET saved_destinations = ? WHERE user_id = 'demo-user-1'", (json.dumps(saved),))
    conn.commit()
    conn.close()

    return {"status": "success", "action": action, "saved_destinations": saved}

@router.get("/reports")
async def get_my_reports():
    reports = RoadReportRepo.get_reports()
    # In demo mode, return reports created by demo user
    return [r for r in reports if r.get("user_id") in ["demo-user-1", "user-reporter-1"]]
