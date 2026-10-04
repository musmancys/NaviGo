import json
import logging
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.db.client import get_supabase_client
from backend.app.db.sqlite_demo import get_db_connection

logger = logging.getLogger("navigo.db.repo")

class DestinationRepo:
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        if not settings.is_demo_mode:
            sb = get_supabase_client()
            if sb:
                try:
                    res = sb.table("destinations").select("*").order("name").execute()
                    return res.data
                except Exception as e:
                    logger.warning("Supabase destination query failed: %s. Using SQLite demo data.", e)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM destinations ORDER BY name")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        for r in rows:
            if isinstance(r.get("tags"), str):
                try:
                    r["tags"] = json.loads(r["tags"])
                except Exception:
                    r["tags"] = []
        return rows

    @staticmethod
    def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        slug = slug.lower().strip()
        if not settings.is_demo_mode:
            sb = get_supabase_client()
            if sb:
                try:
                    res = sb.table("destinations").select("*").eq("slug", slug).single().execute()
                    if res.data:
                        return res.data
                except Exception as e:
                    logger.warning("Supabase get_by_slug failed: %s", e)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM destinations WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        if isinstance(d.get("tags"), str):
            try:
                d["tags"] = json.loads(d["tags"])
            except Exception:
                d["tags"] = []
        return d

class PlaceRepo:
    @staticmethod
    def get_places(destination_slug: Optional[str] = None, place_type: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM places WHERE 1=1"
        params = []
        if destination_slug and destination_slug != "all":
            query += " AND destination_slug = ?"
            params.append(destination_slug.lower())
        if place_type and place_type != "all":
            query += " AND place_type = ?"
            params.append(place_type.lower())
        if search:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

class BusinessRepo:
    @staticmethod
    def get_businesses(destination_slug: Optional[str] = None, business_type: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM businesses WHERE 1=1"
        params = []
        if destination_slug and destination_slug != "all":
            query += " AND destination_slug = ?"
            params.append(destination_slug.lower())
        if business_type and business_type != "all":
            query += " AND business_type = ?"
            params.append(business_type.lower())

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        for r in rows:
            for field in ["photos", "facilities"]:
                if isinstance(r.get(field), str):
                    try:
                        r[field] = json.loads(r[field])
                    except Exception:
                        r[field] = []
        return rows

class RoadReportRepo:
    @staticmethod
    def get_reports(destination_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM road_reports WHERE 1=1"
        params = []
        if destination_slug and destination_slug != "all":
            query += " AND destination_slug = ?"
            params.append(destination_slug.lower())
        query += " ORDER BY created_at DESC LIMIT 50"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        for r in rows:
            for field in ["issue_tags", "ai_analysis_json"]:
                if isinstance(r.get(field), str):
                    try:
                        r[field] = json.loads(r[field])
                    except Exception:
                        pass
        return rows

class AlertRepo:
    @staticmethod
    def get_active(destination_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM alerts WHERE is_active = 1"
        params = []
        if destination_slug and destination_slug != "all":
            query += " AND (destination_slug = ? OR destination_slug IS NULL)"
            params.append(destination_slug.lower())
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
