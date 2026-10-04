import uuid
import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.business import BusinessCreateRequest, BusinessResponse, BusinessDetailResponse, ReviewResponse
from backend.app.db.repositories import BusinessRepo
from backend.app.services.review_summary import summarize_reviews
from backend.app.db.sqlite_demo import get_db_connection

router = APIRouter(prefix="/businesses", tags=["Marketplace"])

@router.get("", response_model=List[BusinessResponse])
async def list_businesses(
    destination: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    verified_only: bool = Query(False)
):
    biz_list = BusinessRepo.get_businesses(destination_slug=destination, business_type=type)
    if verified_only:
        biz_list = [b for b in biz_list if b.get("is_verified")]

    return [
        BusinessResponse(
            id=b["id"],
            destination_slug=b["destination_slug"],
            business_type=b["business_type"],
            name=b["name"],
            contact_name=b.get("contact_name"),
            phone=b.get("phone"),
            email=b.get("email"),
            description=b.get("description"),
            price_range=b.get("price_range"),
            photos=b.get("photos", []),
            facilities=b.get("facilities", []),
            is_verified=bool(b.get("is_verified", 0)),
            verified_at=b.get("verified_at"),
            verified_by=b.get("verified_by"),
            rating=b.get("rating", 4.8),
            created_at=b.get("created_at")
        )
        for b in biz_list
    ]

@router.get("/{business_id}", response_model=BusinessDetailResponse)
async def get_business_detail(business_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Business not found")

    b = dict(row)
    for field in ["photos", "facilities"]:
        if isinstance(b.get(field), str):
            try:
                b[field] = json.loads(b[field])
            except Exception:
                b[field] = []

    # Fetch real stored reviews
    cursor.execute("SELECT * FROM reviews WHERE business_id = ? ORDER BY created_at DESC", (business_id,))
    rev_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    reviews = [
        ReviewResponse(
            id=r["id"],
            business_id=r["business_id"],
            destination_slug=r["destination_slug"],
            user_name=r["user_name"],
            rating=r["rating"],
            comment=r["comment"],
            created_at=r["created_at"]
        )
        for r in rev_rows
    ]

    # If no reviews, provide sample initial tourist review
    if not reviews:
        reviews = [
            ReviewResponse(
                id="rev-init-1",
                business_id=business_id,
                destination_slug=b["destination_slug"],
                user_name="Zubair Ahmed",
                rating=5,
                comment="Clean rooms, hot water was available, and the mountain view from the balcony was incredible.",
                created_at="2026-09-15"
            ),
            ReviewResponse(
                id="rev-init-2",
                business_id=business_id,
                destination_slug=b["destination_slug"],
                user_name="Fatima Noor",
                rating=4,
                comment="Helpful staff and delicious food. Only complaint is the Wi-Fi was slow in the evening.",
                created_at="2026-09-20"
            )
        ]

    ai_summary = await summarize_reviews(business_id, [r.model_dump() for r in reviews])

    return BusinessDetailResponse(
        id=b["id"],
        destination_slug=b["destination_slug"],
        business_type=b["business_type"],
        name=b["name"],
        contact_name=b.get("contact_name"),
        phone=b.get("phone"),
        email=b.get("email"),
        description=b.get("description"),
        price_range=b.get("price_range"),
        photos=b.get("photos", []),
        facilities=b.get("facilities", []),
        is_verified=bool(b.get("is_verified", 0)),
        verified_at=b.get("verified_at"),
        verified_by=b.get("verified_by"),
        rating=b.get("rating", 4.8),
        created_at=b.get("created_at"),
        reviews=reviews,
        ai_summary=ai_summary
    )

@router.post("", response_model=BusinessResponse)
async def register_business(req: BusinessCreateRequest):
    biz_id = f"b-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO businesses (id, user_id, destination_slug, business_type, name, contact_name, phone, email, description, price_range, photos, facilities, is_verified, rating, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 5.0, ?)
    """, (
        biz_id, "user-partner-1", req.destination_slug, req.business_type,
        req.name, req.contact_name, req.phone, req.email, req.description,
        req.price_range, json.dumps(req.photos), json.dumps(req.facilities), now_iso
    ))
    conn.commit()
    conn.close()

    return BusinessResponse(
        id=biz_id,
        destination_slug=req.destination_slug,
        business_type=req.business_type,
        name=req.name,
        contact_name=req.contact_name,
        phone=req.phone,
        email=req.email,
        description=req.description,
        price_range=req.price_range,
        photos=req.photos,
        facilities=req.facilities,
        is_verified=False,
        rating=5.0,
        created_at=now_iso
    )
