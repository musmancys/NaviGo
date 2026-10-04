import os
import sys
import time
import httpx
import uuid
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.db.sqlite_demo import get_db_connection

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Destination coordinates with bounding radius
TARGETS = [
    {"slug": "naran", "lat": 34.9089, "lng": 73.6528, "radius": 15000},
    {"slug": "hunza", "lat": 36.3167, "lng": 74.6500, "radius": 20000},
    {"slug": "skardu", "lat": 35.2971, "lng": 75.6333, "radius": 20000},
    {"slug": "swat", "lat": 35.2227, "lng": 72.4258, "radius": 20000},
    {"slug": "murree", "lat": 33.9070, "lng": 73.3943, "radius": 12000}
]

def fetch_overpass_pois(slug: str, lat: float, lng: float, radius: int):
    query = f"""
    [out:json][timeout:25];
    (
      node["tourism"~"attraction|viewpoint|hotel|guest_house"](around:{radius},{lat},{lng});
      node["amenity"~"restaurant|hospital|fuel|atm"](around:{radius},{lat},{lng});
    );
    out body 25;
    """
    headers = {"User-Agent": "NaviGo-Tourism-Bot/1.0 (dev@navigo.app)"}
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(OVERPASS_URL, data={"data": query}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get("elements", [])
                print(f"[{slug.upper()}] Fetched {len(elements)} POIs from Overpass OSM.")
                return elements
    except Exception as e:
        print(f"[{slug.upper()}] Overpass request failed: {e}")
    return []

def map_osm_element(slug: str, elem: dict):
    tags = elem.get("tags", {})
    name = tags.get("name:en") or tags.get("name")
    if not name:
        return None

    place_type = "attraction"
    icon = "🏔️"

    if tags.get("tourism") in ["hotel", "guest_house"] or tags.get("amenity") == "hotel":
        place_type = "hotel"
        icon = "🏨"
    elif tags.get("amenity") == "restaurant":
        place_type = "restaurant"
        icon = "🍽️"
    elif tags.get("amenity") == "fuel":
        place_type = "fuel"
        icon = "⛽"
    elif tags.get("amenity") in ["hospital", "clinic", "doctors"]:
        place_type = "hospital"
        icon = "🏥"
    elif tags.get("amenity") in ["atm", "bank"]:
        place_type = "atm"
        icon = "🏧"

    return {
        "id": f"osm-{elem['id']}",
        "destination_slug": slug,
        "name": name,
        "place_type": place_type,
        "icon": icon,
        "latitude": elem["lat"],
        "longitude": elem["lon"],
        "map_x": 50.0,
        "map_y": 50.0,
        "description": tags.get("description") or f"Point of interest in {slug.title()}.",
        "price_level": "Standard",
        "rating": 4.5,
        "address": f"{name}, {slug.title()}, Pakistan",
        "contact_phone": tags.get("phone", "+92 300 0000000"),
        "is_verified": 0,
        "created_at": datetime.datetime.now().isoformat()
    }

def seed_overpass():
    conn = get_db_connection()
    cursor = conn.cursor()
    total_added = 0

    for target in TARGETS:
        pois = fetch_overpass_pois(target["slug"], target["lat"], target["lng"], target["radius"])
        for elem in pois:
            mapped = map_osm_element(target["slug"], elem)
            if mapped:
                cursor.execute("""
                INSERT OR IGNORE INTO places (id, destination_slug, name, place_type, icon, latitude, longitude, map_x, map_y, description, price_level, rating, address, contact_phone, is_verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mapped["id"], mapped["destination_slug"], mapped["name"], mapped["place_type"], mapped["icon"],
                    mapped["latitude"], mapped["longitude"], mapped["map_x"], mapped["map_y"], mapped["description"],
                    mapped["price_level"], mapped["rating"], mapped["address"], mapped["contact_phone"], mapped["is_verified"],
                    mapped["created_at"]
                ))
                total_added += 1
        time.sleep(1.0) # Polite 1 req/s rate limit

    conn.commit()
    conn.close()
    print(f"Successfully processed Overpass seed. Added/verified {total_added} points of interest.")

if __name__ == "__main__":
    seed_overpass()
