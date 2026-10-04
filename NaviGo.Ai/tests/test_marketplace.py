import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_list_businesses():
    response = client.get("/api/businesses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Verified flag and fields present
    assert any(b["is_verified"] is True for b in data)

def test_business_detail_and_ai_summary():
    # Get first business
    businesses = client.get("/api/businesses").json()
    b_id = businesses[0]["id"]

    detail_resp = client.get(f"/api/businesses/{b_id}")
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["id"] == b_id
    assert "reviews" in data
    assert "ai_summary" in data
    assert len(data["ai_summary"]["pros"]) > 0

def test_create_review():
    businesses = client.get("/api/businesses").json()
    b_id = businesses[0]["id"]

    rev_payload = {
        "business_id": b_id,
        "destination_slug": "naran",
        "user_name": "Hamza Tariq",
        "rating": 5,
        "comment": "Exceptional hospitality, clean bed sheets, and delicious trout fish dinner."
    }
    rev_resp = client.post("/api/reviews", json=rev_payload)
    assert rev_resp.status_code == 200
    data = rev_resp.json()
    assert data["user_name"] == "Hamza Tariq"
    assert data["rating"] == 5

def test_admin_verification_flow():
    # 1. Register unverified business
    new_biz = {
        "destination_slug": "hunza",
        "business_type": "hotel",
        "name": "Eagle Nest Hotel Hunza",
        "contact_name": "Karim Beg",
        "phone": "+92 300 1234567",
        "description": "Panoramic view hotel on Duikar hill.",
        "price_range": "Rs. 12,000/night"
    }
    create_resp = client.post("/api/businesses", json=new_biz)
    assert create_resp.status_code == 200
    biz = create_resp.json()
    assert biz["is_verified"] is False

    # 2. Verify via admin endpoint
    verify_resp = client.post(
        f"/api/admin/verify-business/{biz['id']}",
        json={"verified_by": "Gilgit-Baltistan Tourism Dept", "verified_at": "September 2026"}
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["success"] is True

    # 3. Check detail reflects verification
    updated = client.get(f"/api/businesses/{biz['id']}").json()
    assert updated["is_verified"] is True
    assert updated["verified_at"] == "September 2026"
