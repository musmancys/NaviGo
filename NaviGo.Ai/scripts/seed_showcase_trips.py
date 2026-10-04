import os
import sys
import json
import sqlite3
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.db.sqlite_demo import get_db_connection, init_demo_db

SHOWCASE_TRIPS = [
    {
        "id": "trip-showcase-1",
        "destination_slug": "naran",
        "title": "Naran Adventure",
        "duration_days": 3,
        "travelers_count": 4,
        "budget_pkr": 35000,
        "transport_type": "car",
        "status": "completed",
        "share_slug": "naran-adventure",
        "interests": ["Lakes", "Mountains", "Rivers"],
        "days": [
            {
                "day_number": 1,
                "title": "Arrival & Kunhar River Breeze",
                "places": [
                    {"name": "Kunhar River Rafting", "type": "attraction", "time": "14:00", "notes": "Scenic river bank stroll and trout dinner"}
                ]
            },
            {
                "day_number": 2,
                "title": "Lake Saif-ul-Malook Excursion",
                "places": [
                    {"name": "Saif-ul-Malook Lake", "type": "attraction", "time": "09:30", "notes": "Iconic fairy-tale alpine lake by 4x4 jeep"}
                ]
            },
            {
                "day_number": 3,
                "title": "Babusar Pass Vista & Return",
                "places": [
                    {"name": "Babusar Top", "type": "attraction", "time": "10:00", "notes": "High mountain pass at 4,173m elevation"}
                ]
            }
        ],
        "budget": {"transport": 12000, "accommodation": 14000, "food": 6000, "activities": 3000, "total": 35000}
    },
    {
        "id": "trip-showcase-2",
        "destination_slug": "hunza",
        "title": "Hunza Explorer",
        "duration_days": 5,
        "travelers_count": 2,
        "budget_pkr": 60000,
        "transport_type": "car",
        "status": "completed",
        "share_slug": "hunza-explorer",
        "interests": ["Culture", "Forts", "Scenic"],
        "days": [
            {
                "day_number": 1,
                "title": "Karimabad & Baltit Fort",
                "places": [
                    {"name": "Baltit Fort", "type": "attraction", "time": "11:00", "notes": "700-year-old UNESCO heritage fort"}
                ]
            },
            {
                "day_number": 2,
                "title": "Altit Fort & Royal Garden",
                "places": [
                    {"name": "Altit Fort", "type": "attraction", "time": "10:00", "notes": "Ancient royal residence overlooking KKH"}
                ]
            },
            {
                "day_number": 3,
                "title": "Attabad Lake Boating",
                "places": [
                    {"name": "Attabad Lake", "type": "attraction", "time": "11:30", "notes": "Turquoise glacial waters and jet skiing"}
                ]
            },
            {
                "day_number": 4,
                "title": "Passu Cones & Suspension Bridge",
                "places": [
                    {"name": "Passu Cones", "type": "attraction", "time": "09:00", "notes": "Cathedral mountain spires & suspension bridge"}
                ]
            },
            {
                "day_number": 5,
                "title": "Local Crafts & Departure",
                "places": [
                    {"name": "Karimabad Bazaar", "type": "attraction", "time": "10:00", "notes": "Local dried fruits, gemstones, and handicrafts"}
                ]
            }
        ],
        "budget": {"transport": 22000, "accommodation": 24000, "food": 9000, "activities": 5000, "total": 60000}
    },
    {
        "id": "trip-showcase-3",
        "destination_slug": "skardu",
        "title": "Skardu Expedition",
        "duration_days": 7,
        "travelers_count": 6,
        "budget_pkr": 95000,
        "transport_type": "jeep",
        "status": "upcoming",
        "share_slug": "skardu-expedition",
        "interests": ["Adventure", "Lakes", "Deserts"],
        "days": [
            {
                "day_number": 1,
                "title": "Shangrila Resort & Lower Kachura",
                "places": [
                    {"name": "Shangrila Resort", "type": "attraction", "time": "12:00", "notes": "Pagoda-style resort on circular lake"}
                ]
            },
            {
                "day_number": 2,
                "title": "Upper Kachura Lake Trek",
                "places": [
                    {"name": "Upper Kachura Lake", "type": "attraction", "time": "09:30", "notes": "Pristine trout lake & local apricots"}
                ]
            },
            {
                "day_number": 3,
                "title": "Cold Desert of Katpana",
                "places": [
                    {"name": "Sarfaranga Cold Desert", "type": "attraction", "time": "15:00", "notes": "High-altitude sand dunes with snow backdrop"}
                ]
            },
            {
                "day_number": 4,
                "title": "Shigar Valley & Palace",
                "places": [
                    {"name": "Shigar Fort", "type": "attraction", "time": "10:30", "notes": "Restored 17th-century Raja palace"}
                ]
            },
            {
                "day_number": 5,
                "title": "Deosai Plains Wildlife Safari",
                "places": [
                    {"name": "Deosai National Park", "type": "attraction", "time": "08:00", "notes": "Land of Giants plateau and brown bears"}
                ]
            },
            {
                "day_number": 6,
                "title": "Sheosar Lake Wilderness",
                "places": [
                    {"name": "Sheosar Lake", "type": "attraction", "time": "11:00", "notes": "Heart-shaped high altitude alpine lake"}
                ]
            },
            {
                "day_number": 7,
                "title": "Skardu Bazaar & Departure",
                "places": [
                    {"name": "Skardu City", "type": "attraction", "time": "09:00", "notes": "Local walnut cakes and traditional shawls"}
                ]
            }
        ],
        "budget": {"transport": 38000, "accommodation": 35000, "food": 14000, "activities": 8000, "total": 95000}
    },
    {
        "id": "trip-showcase-4",
        "destination_slug": "kashmir",
        "title": "Kashmir Dreams",
        "duration_days": 10,
        "travelers_count": 4,
        "budget_pkr": 80000,
        "transport_type": "car",
        "status": "draft",
        "share_slug": "kashmir-dreams",
        "interests": ["Valleys", "Lakes", "Pine Forests"],
        "days": [
            {
                "day_number": 1,
                "title": "Muzaffarabad Confluence",
                "places": [
                    {"name": "Red Fort Muzaffarabad", "type": "attraction", "time": "14:00", "notes": "Neelum and Jhelum rivers meeting point"}
                ]
            },
            {
                "day_number": 2,
                "title": "Neelum Valley & Kutton Waterfall",
                "places": [
                    {"name": "Kutton Jagran", "type": "attraction", "time": "11:00", "notes": "Lush pine valley waterfall resort"}
                ]
            },
            {
                "day_number": 3,
                "title": "Keran Riverbank Vista",
                "places": [
                    {"name": "Keran Village", "type": "attraction", "time": "10:00", "notes": "Neelum river boundary and wooden lodges"}
                ]
            },
            {
                "day_number": 4,
                "title": "Ancient Sharda Peeth",
                "places": [
                    {"name": "Sharda Ruins", "type": "attraction", "time": "11:00", "notes": "Historic stone temple university"}
                ]
            },
            {
                "day_number": 5,
                "title": "Kel to Arang Kel Hike",
                "places": [
                    {"name": "Arang Kel", "type": "attraction", "time": "09:00", "notes": "Pearl of Neelum cable lift & lush meadows"}
                ]
            }
        ],
        "budget": {"transport": 30000, "accommodation": 32000, "food": 12000, "activities": 6000, "total": 80000}
    },
    {
        "id": "trip-showcase-5",
        "destination_slug": "swat",
        "title": "Weekend in Swat",
        "duration_days": 2,
        "travelers_count": 3,
        "budget_pkr": 25000,
        "transport_type": "car",
        "status": "completed",
        "share_slug": "weekend-in-swat",
        "interests": ["Nature", "Rivers", "Relaxation"],
        "days": [
            {
                "day_number": 1,
                "title": "White Palace & Mingora",
                "places": [
                    {"name": "White Palace Marghazar", "type": "attraction", "time": "11:00", "notes": "Swat royal white marble palace"}
                ]
            },
            {
                "day_number": 2,
                "title": "Malam Jabba Ski Resort",
                "places": [
                    {"name": "Malam Jabba", "type": "attraction", "time": "09:30", "notes": "Chairlift ride and alpine views"}
                ]
            }
        ],
        "budget": {"transport": 10000, "accommodation": 9000, "food": 4000, "activities": 2000, "total": 25000}
    },
    {
        "id": "trip-showcase-6",
        "destination_slug": "fairy-meadows",
        "title": "Fairy Meadows Camp",
        "duration_days": 14,
        "travelers_count": 5,
        "budget_pkr": 110000,
        "transport_type": "jeep",
        "status": "draft",
        "share_slug": "fairy-meadows-camp",
        "interests": ["Trekking", "Nanga Parbat", "Camping"],
        "days": [
            {
                "day_number": 1,
                "title": "Raikhot Bridge & Jeep Safari",
                "places": [
                    {"name": "Raikhot Jeep Track", "type": "attraction", "time": "08:00", "notes": "Mountain cliff road up to Tattu"}
                ]
            },
            {
                "day_number": 2,
                "title": "Fairy Meadows Basecamp Trek",
                "places": [
                    {"name": "Fairy Meadows Plateau", "type": "attraction", "time": "09:00", "notes": "Direct front vista of Nanga Parbat north face"}
                ]
            },
            {
                "day_number": 3,
                "title": "Beyal Camp & Glacier Viewpoint",
                "places": [
                    {"name": "Beyal Camp", "type": "attraction", "time": "10:00", "notes": "Raikhot glacier edge and alpine huts"}
                ]
            }
        ],
        "budget": {"transport": 45000, "accommodation": 38000, "food": 17000, "activities": 10000, "total": 110000}
    }
]

def seed_showcase():
    init_demo_db()
    conn = get_db_connection()
    c = conn.cursor()

    # Clear duplicate test-generated trips
    c.execute("DELETE FROM trips WHERE id NOT LIKE 'trip-showcase-%'")

    for idx, t in enumerate(SHOWCASE_TRIPS):
        created_time = (datetime.datetime.now() - datetime.timedelta(days=idx*3)).isoformat()
        c.execute("""
        INSERT OR REPLACE INTO trips (id, user_id, destination_slug, title, duration_days, travelers_count, budget_pkr, transport_type, interests, itinerary_json, budget_breakdown_json, status, share_slug, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t["id"], "demo-user-1", t["destination_slug"], t["title"],
            t["duration_days"], t["travelers_count"], t["budget_pkr"],
            t["transport_type"], json.dumps(t["interests"]),
            json.dumps(t["days"]), json.dumps(t["budget"]),
            t["status"], t["share_slug"], created_time, created_time
        ))

    conn.commit()
    count = c.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"Successfully seeded {count} canonical showcase trips into database!")
    conn.close()

if __name__ == "__main__":
    seed_showcase()
