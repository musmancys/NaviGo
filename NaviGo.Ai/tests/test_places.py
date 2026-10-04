import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_list_places():
    response = client.get("/api/places")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Verify Naran attractions exist
    names = [p["name"] for p in data]
    assert any("Saif-ul-Malook" in n for n in names)

def test_filter_places_by_destination():
    response = client.get("/api/places?destination=hunza")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for p in data:
        assert p["destination_slug"] == "hunza"

def test_filter_places_by_type():
    response = client.get("/api/places?type=hospital")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for p in data:
        assert p["place_type"] == "hospital"

def test_nearby_places():
    # Coords near Naran center
    response = client.get("/api/places/nearby?lat=34.9089&lng=73.6528&radius_km=30")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # First item should have distance_km
    assert data[0]["distance_km"] is not None
    # Distance should be ascending
    distances = [p["distance_km"] for p in data]
    assert distances == sorted(distances)
