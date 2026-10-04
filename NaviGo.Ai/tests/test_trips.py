import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.budget import calculate_trip_budget

client = TestClient(app)

def test_deterministic_budget_calculator():
    res = calculate_trip_budget(
        duration_days=3,
        travelers_count=4,
        target_budget_pkr=35000,
        transport_type="car"
    )
    assert res["target_budget_pkr"] == 35000
    assert res["total_estimated_pkr"] > 0
    assert "breakdown" in res
    assert res["breakdown"]["transport"] == 21000 # 7000 * 3 days
    assert res["breakdown"]["hotel"] > 0
    assert res["breakdown"]["food"] > 0
    assert res["status"] in ["Within Budget", "Close to Budget", "Over Budget"]

def test_trips_list():
    response = client.get("/api/trips")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_trip_plan_sse():
    payload = {
        "origin": "Islamabad",
        "destination_slug": "naran",
        "duration_days": 3,
        "travelers_count": 4,
        "budget_pkr": 35000,
        "transport_type": "car",
        "interests": ["nature", "adventure"]
    }
    with client.stream("POST", "/api/trips/plan", json=payload) as response:
        assert response.status_code == 200
        content = "".join([chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_lines()])
        assert "event: step" in content or "event: complete" in content

def test_trip_pdf_export():
    # First get trips list to get an ID
    trips = client.get("/api/trips").json()
    trip_id = trips[0]["id"]
    pdf_resp = client.get(f"/api/trips/{trip_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
