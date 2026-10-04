import io
import sys
import os
import json
import httpx
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def generate_test_image_bytes():
    img = Image.new("RGB", (100, 100), color=(100, 140, 170))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_smoke_test(base_url: str):
    print(f"==================================================")
    print(f">> NaviGo End-to-End Smoke Test Suite")
    print(f"Target URL: {base_url}")
    print(f"==================================================")

    client = httpx.Client(base_url=base_url, timeout=15.0)
    passed = 0
    failed = 0

    tests = [
        ("Root Frontend (GET /)", "get", "/", None, None, 200, lambda r: "NaviGo" in r.text),
        ("Health Check (GET /api/health)", "get", "/api/health", None, None, 200, lambda r: r.json().get("status") == "ok"),
        ("Public Config (GET /api/config)", "get", "/api/config", None, None, 200, lambda r: "demo_mode" in r.json()),
        ("Destinations List (GET /api/destinations)", "get", "/api/destinations", None, None, 200, lambda r: len(r.json()) >= 8),
        ("Destination Detail (GET /api/destinations/naran)", "get", "/api/destinations/naran", None, None, 200, lambda r: "weather" in r.json()),
        ("Live Weather (GET /api/weather/hunza)", "get", "/api/weather/hunza", None, None, 200, lambda r: "temp" in r.json()),
        ("Places Catalog (GET /api/places)", "get", "/api/places", None, None, 200, lambda r: len(r.json()) > 0),
        ("Nearby Places (GET /api/places/nearby)", "get", "/api/places/nearby?lat=34.9089&lng=73.6528&radius_km=30", None, None, 200, lambda r: len(r.json()) > 0),
        ("Grounded Chat (POST /api/chat)", "post", "/api/chat", {"message": "What is the weather in Naran?", "destination_slug": "naran"}, None, 200, lambda r: "text" in r.json() and len(r.json().get("cards", [])) > 0),
        ("Voice Parsing (POST /api/voice/parse)", "post", "/api/voice/parse", None, {"transcript": "Mujhe Lahore se 3 din ke liye Naran jana hai, budget 40 hazar hai"}, 200, lambda r: r.json().get("params", {}).get("budget_pkr") == 40000),
        ("Marketplace Businesses (GET /api/businesses)", "get", "/api/businesses", None, None, 200, lambda r: len(r.json()) > 0),
        ("Travel Alerts (GET /api/alerts)", "get", "/api/alerts", None, None, 200, lambda r: len(r.json()) > 0),
        ("Community Road Reports (GET /api/reports)", "get", "/api/reports", None, None, 200, lambda r: len(r.json()) > 0),
    ]

    for name, method, endpoint, json_data, form_data, expected_status, validator in tests:
        try:
            if method == "get":
                res = client.get(endpoint)
            elif method == "post":
                if json_data:
                    res = client.post(endpoint, json=json_data)
                elif form_data:
                    res = client.post(endpoint, data=form_data)
                else:
                    res = client.post(endpoint)

            if res.status_code == expected_status and validator(res):
                print(f"  [PASS] {name} ({res.status_code})")
                passed += 1
            else:
                print(f"  [FAIL] {name} - Status: {res.status_code}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] {name} - Exception: {e}")
            failed += 1

    # Test Vision Multipart Upload
    try:
        img_bytes = generate_test_image_bytes()
        files = {"file": ("test_road.jpg", img_bytes, "image/jpeg")}
        res = client.post("/api/vision/road", files=files)
        if res.status_code == 200 and res.json().get("is_road_photo") is True and "disclaimer" in res.json():
            print(f"  [PASS] Vision AI Photo Analysis (POST /api/vision/road) (200)")
            passed += 1
        else:
            print(f"  [FAIL] Vision AI Photo Analysis - Status: {res.status_code}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] Vision AI Photo Analysis - Exception: {e}")
        failed += 1

    # Test SSE Stream for Trip Planner
    try:
        plan_req = {
            "origin": "Islamabad",
            "destination_slug": "naran",
            "duration_days": 3,
            "travelers_count": 4,
            "budget_pkr": 35000,
            "transport_type": "car"
        }
        with client.stream("POST", "/api/trips/plan", json=plan_req) as sse_res:
            if sse_res.status_code == 200:
                print(f"  [PASS] AI Trip Planner SSE Stream (POST /api/trips/plan) (200)")
                passed += 1
            else:
                print(f"  [FAIL] AI Trip Planner SSE Stream - Status: {sse_res.status_code}")
                failed += 1
    except Exception as e:
        print(f"  [FAIL] AI Trip Planner SSE Stream - Exception: {e}")
        failed += 1

    print(f"==================================================")
    print(f"Results: {passed} PASSED, {failed} FAILED")
    print(f"==================================================")

    if failed > 0:
        sys.exit(1)
    print("ALL CRITICAL PATHS VERIFIED CLEANLY!")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.getenv("BASE_URL", "http://localhost:8000")
    run_smoke_test(target)
