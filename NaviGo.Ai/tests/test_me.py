import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_my_profile():
    response = client.get("/api/me/profile")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "full_name" in data
    assert "saved_destinations" in data
    assert isinstance(data["saved_destinations"], list)

def test_update_my_profile():
    update_payload = {"full_name": "Tayyab Traveler", "preferred_language": "ur"}
    response = client.put("/api/me/profile", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Tayyab Traveler"
    assert data["preferred_language"] == "ur"

def test_saved_destinations_toggle():
    # Toggle save for skardu
    response = client.post("/api/me/saved/skardu")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "skardu" in data["saved_destinations"]

    # Retrieve saved
    saved_list = client.get("/api/me/saved").json()
    slugs = [d["slug"] for d in saved_list]
    assert "skardu" in slugs

    # Untoggle
    untoggle = client.post("/api/me/saved/skardu").json()
    assert "skardu" not in untoggle["saved_destinations"]

def test_my_reports():
    response = client.get("/api/me/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
