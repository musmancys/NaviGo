import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.weather_rules import evaluate_activity_safety
from backend.app.config import settings

client = TestClient(app)

def test_weather_rules_safety_evaluation():
    # Babusar Pass in freezing weather
    freezing_weather = {"temp": -2, "cond": "Snow", "wind_kmh": 20, "precip_probability": 40}
    is_safe, reason, alt = evaluate_activity_safety(
        activity_name="Crossing Babusar Top pass",
        place_name="Babusar Top",
        weather=freezing_weather,
        road_reports=[]
    )
    assert is_safe is False
    assert "Sub-zero" in reason or "snow" in reason.lower()
    assert alt is not None

    # Normal weather is safe
    clear_weather = {"temp": 20, "cond": "Clear", "wind_kmh": 10, "precip_probability": 0}
    is_safe_2, reason_2, alt_2 = evaluate_activity_safety(
        activity_name="Sightseeing",
        place_name="Naran Bazaar",
        weather=clear_weather,
        road_reports=[]
    )
    assert is_safe_2 is True
    assert reason_2 is None

def test_replan_trip_flow():
    # Create or plan a trip first
    plan_payload = {
        "origin": "Islamabad",
        "destination_slug": "naran",
        "duration_days": 3,
        "travelers_count": 4,
        "budget_pkr": 35000,
        "transport_type": "car",
        "interests": ["nature", "adventure"]
    }
    # Retrieve existing trip from /trips
    trips_resp = client.get("/api/trips")
    trips = trips_resp.json()
    trip_id = trips[0]["id"]

    # Trigger replan with simulated landslide hazard
    replan_resp = client.post(
        f"/api/trips/replan?trip_id={trip_id}&simulated_hazard=Heavy rain and landslide warning"
    )
    assert replan_resp.status_code == 200
    data = replan_resp.json()
    assert "trip_id" in data
    assert "explanation" in data
    assert "adjusted_days" in data

def test_internal_cron_weather_alerts_auth():
    # Unauthorized request without secret
    unauth_resp = client.post("/api/internal/cron/weather-alerts")
    assert unauth_resp.status_code == 401

    # Authorized request with secret
    auth_resp = client.post(
        "/api/internal/cron/weather-alerts",
        headers={"Authorization": f"Bearer {settings.cron_secret}"}
    )
    assert auth_resp.status_code == 200
    data = auth_resp.json()
    assert data["status"] == "success"
    assert data["checked_destinations_count"] >= 8
