import sqlite3
import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("navigo.db.sqlite")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "demo_navigo.db")

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_demo_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS destinations (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        sub_title TEXT,
        about TEXT,
        hero_image_url TEXT,
        from_price_pkr INTEGER,
        tags TEXT, -- JSON array
        best_season TEXT,
        latitude REAL,
        longitude REAL,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS places (
        id TEXT PRIMARY KEY,
        destination_slug TEXT NOT NULL,
        name TEXT NOT NULL,
        place_type TEXT NOT NULL, -- attraction, hotel, restaurant, fuel, hospital, atm, guide
        icon TEXT,
        latitude REAL,
        longitude REAL,
        map_x REAL,
        map_y REAL,
        description TEXT,
        price_level TEXT,
        rating REAL,
        address TEXT,
        contact_phone TEXT,
        is_verified INTEGER DEFAULT 0,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS trips (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        destination_slug TEXT,
        title TEXT,
        duration_days INTEGER,
        travelers_count INTEGER,
        budget_pkr INTEGER,
        transport_type TEXT,
        interests TEXT, -- JSON array
        itinerary_json TEXT, -- JSON structure
        budget_breakdown_json TEXT, -- JSON
        status TEXT, -- draft, upcoming, completed
        share_slug TEXT UNIQUE,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS road_reports (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        destination_slug TEXT,
        road_name TEXT NOT NULL,
        status TEXT NOT NULL, -- open, caution, closed
        issue_tags TEXT, -- JSON array
        severity TEXT, -- low, medium, high, severe
        confidence REAL,
        ai_analysis_json TEXT,
        photo_url TEXT,
        latitude REAL,
        longitude REAL,
        confirmations_count INTEGER DEFAULT 0,
        cleared_votes_count INTEGER DEFAULT 0,
        is_authority_override INTEGER DEFAULT 0,
        created_at TEXT,
        expires_at TEXT
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        destination_slug TEXT,
        title TEXT NOT NULL,
        description TEXT,
        alert_type TEXT, -- road_closure, weather_warning, landslide, flooding, traffic, security
        severity TEXT, -- info, warning, emergency
        source TEXT, -- authority, ai_weather_cron, high_confidence_report
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        expires_at TEXT
    );

    CREATE TABLE IF NOT EXISTS businesses (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        destination_slug TEXT,
        business_type TEXT, -- hotel, guide, jeep, restaurant, camping, adventure, handicrafts
        name TEXT NOT NULL,
        contact_name TEXT,
        phone TEXT,
        email TEXT,
        description TEXT,
        price_range TEXT,
        photos TEXT, -- JSON array
        facilities TEXT, -- JSON array
        is_verified INTEGER DEFAULT 0,
        verified_at TEXT,
        verified_by TEXT,
        rating REAL,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY,
        business_id TEXT,
        destination_slug TEXT,
        user_id TEXT,
        user_name TEXT,
        rating INTEGER,
        comment TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS price_catalog (
        id TEXT PRIMARY KEY,
        item_key TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL, -- transport, hotel, food, activities, other
        base_price_pkr INTEGER NOT NULL,
        unit TEXT NOT NULL, -- per_day, per_person_per_day, fixed
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        user_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'tourist', -- tourist, business, authority, admin
        preferred_language TEXT DEFAULT 'en',
        saved_destinations TEXT, -- JSON array of slugs
        created_at TEXT
    );
    """)

    conn.commit()
    conn.close()
    logger.info("Demo SQLite database initialized at %s", DB_PATH)
