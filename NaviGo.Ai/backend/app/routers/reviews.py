import uuid
import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.business import ReviewCreateRequest, ReviewResponse
from backend.app.db.sqlite_demo import get_db_connection

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("", response_model=List[ReviewResponse])
async def list_reviews(business_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE business_id = ? ORDER BY created_at DESC", (business_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return [
        ReviewResponse(
            id=r["id"],
            business_id=r["business_id"],
            destination_slug=r["destination_slug"],
            user_name=r["user_name"],
            rating=r["rating"],
            comment=r["comment"],
            created_at=r["created_at"]
        )
        for r in rows
    ]

@router.post("", response_model=ReviewResponse)
async def create_review(req: ReviewCreateRequest):
    rev_id = f"rev-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO reviews (id, business_id, destination_slug, user_id, user_name, rating, comment, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rev_id, req.business_id, req.destination_slug, "demo-user-1",
        req.user_name, req.rating, req.comment, now_iso
    ))
    conn.commit()
    conn.close()

    return ReviewResponse(
        id=rev_id,
        business_id=req.business_id,
        destination_slug=req.destination_slug,
        user_name=req.user_name,
        rating=req.rating,
        comment=req.comment,
        created_at=now_iso
    )
