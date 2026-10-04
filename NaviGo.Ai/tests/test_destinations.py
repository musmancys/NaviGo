import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_list_destinations():
    response = client.get("/api/destinations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8
    slugs = [d["slug"] for d in data]
    assert "naran" in slugs
    assert "hunza" in slugs
    assert "skardu" in slugs

def test_get_destination_detail():
    response = client.get("/api/destinations/naran")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "naran"
    assert data["name"] == "Naran"
    assert "weather" in data
    assert "temp" in data["weather"]
    assert "road_status" in data
    assert len(data["popular_places"]) > 0
    assert len(data["verified_businesses"]) > 0

def test_get_weather_by_slug():
    response = client.get("/api/weather/hunza")
    assert response.status_code == 200
    data = response.json()
    assert "temp" in data
    assert "cond" in data
    assert "high" in data
    assert "low" in data

def test_destination_not_found():
    response = client.get("/api/destinations/nonexistent-place-xyz")
    assert response.status_code == 404
