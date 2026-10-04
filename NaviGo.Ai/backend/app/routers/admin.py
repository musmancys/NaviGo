from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.db.sqlite_demo import get_db_connection

router = APIRouter(prefix="/admin", tags=["Admin & Authority"])

class VerifyBusinessRequest(BaseModel):
    verified_by: str = "Tourism Directorate KPK"
    verified_at: str = "September 2026"

class UpdatePriceRequest(BaseModel):
    base_price_pkr: int
    notes: str = ""

@router.post("/verify-business/{business_id}")
async def verify_business(business_id: str, req: VerifyBusinessRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE businesses
    SET is_verified = 1, verified_at = ?, verified_by = ?
    WHERE id = ?
    """, (req.verified_at, req.verified_by, business_id))
    conn.commit()
    cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Business not found")

    return {
        "success": True,
        "message": f"Business '{dict(row)['name']}' verified successfully.",
        "verified_at": req.verified_at,
        "verified_by": req.verified_by
    }

@router.get("/price-catalog")
async def list_price_catalog():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM price_catalog ORDER BY category")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@router.put("/price-catalog/{key}")
async def update_price_item(key: str, req: UpdatePriceRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE price_catalog
    SET base_price_pkr = ?, notes = ?
    WHERE item_key = ?
    """, (req.base_price_pkr, req.notes, key))
    conn.commit()
    conn.close()
    return {"success": True, "key": key, "new_price": req.base_price_pkr}
