import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "demo_mode" in data
    assert "timestamp" in data

def test_config_endpoint():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "demo_mode" in data
    assert "public_base_url" in data
    assert "supabase_anon_key" in data

def test_root_serves_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert "NaviGo" in response.text
