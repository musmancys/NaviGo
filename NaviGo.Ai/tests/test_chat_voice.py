import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_chat_weather_intent():
    response = client.post("/api/chat", json={
        "message": "What is the weather in Naran?",
        "destination_slug": "naran"
    })
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "cards" in data
    assert len(data["cards"]) > 0
    # Weather keywords present
    assert any("°C" in c["title"] for c in data["cards"])

def test_chat_road_intent():
    response = client.post("/api/chat", json={
        "message": "Is the road open to Babusar?",
        "destination_slug": "naran"
    })
    assert response.status_code == 200
    data = response.json()
    assert "road" in data["text"].lower() or "status" in data["text"].lower()
    assert len(data["cards"]) > 0

def test_chat_budget_intent():
    response = client.post("/api/chat", json={
        "message": "How much budget do I need for 4 people?",
        "destination_slug": "naran"
    })
    assert response.status_code == 200
    data = response.json()
    assert "Rs." in data["text"]
    assert len(data["cards"]) > 0

def test_voice_parse_urdu_numerals():
    transcript = "Mujhe Lahore se 3 din ke liye Naran jana hai, budget 40 hazar hai"
    response = client.post("/api/voice/parse", data={"transcript": transcript})
    assert response.status_code == 200
    data = response.json()
    assert data["params"]["origin"] == "Lahore"
    assert data["params"]["destination"] == "naran"
    assert data["params"]["duration_days"] == 3
    assert data["params"]["budget_pkr"] == 40000

def test_voice_parse_english():
    transcript = "I want to visit Hunza from Islamabad for 5 days with 2 people"
    response = client.post("/api/voice/parse", data={"transcript": transcript})
    assert response.status_code == 200
    data = response.json()
    assert data["params"]["destination"] == "hunza"
    assert data["params"]["duration_days"] == 5
    assert data["params"]["travelers"] == 2
