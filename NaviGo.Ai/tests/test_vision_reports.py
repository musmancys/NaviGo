import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def create_test_image_bytes():
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_vision_road_upload():
    img_bytes = create_test_image_bytes()
    response = client.post(
        "/api/vision/road",
        files={"file": ("road_mud.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_road_photo"] is True
    assert "issues" in data
    assert "severity" in data
    assert "disclaimer" in data
    assert "AI suggestion" in data["disclaimer"]

def test_community_reports_flow():
    # 1. List reports
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    initial_reports = resp.json()

    # 2. Create new report
    new_rep_payload = {
        "destination_slug": "naran",
        "road_name": "Kaghan Road Mile 14",
        "status": "caution",
        "issue_tags": ["Mud", "Standing Water"],
        "severity": "medium",
        "confidence": 0.88,
        "summary": "Water crossing road after rain"
    }
    create_resp = client.post("/api/reports", json=new_rep_payload)
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["road_name"] == "Kaghan Road Mile 14"
    assert created["confirmations_count"] == 1

    # 3. Vote on report
    vote_resp = client.post(f"/api/reports/{created['id']}/vote", json={"vote_type": "confirm"})
    assert vote_resp.status_code == 200
    assert vote_resp.json()["confirmations"] == 2

def test_alerts_list():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "title" in data[0]
    assert "severity" in data[0]
