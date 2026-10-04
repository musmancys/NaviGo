import logging
from typing import Optional
from backend.app.config import settings
from backend.app.db.sqlite_demo import init_demo_db, get_db_connection

logger = logging.getLogger("navigo.db")

_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.supabase_url and settings.supabase_anon_key:
        try:
            from supabase import create_client, Client
            key = settings.supabase_service_role_key or settings.supabase_anon_key
            _supabase_client = create_client(settings.supabase_url, key)
            logger.info("Connected to Supabase at %s", settings.supabase_url)
            return _supabase_client
        except Exception as e:
            logger.error("Failed to initialize Supabase client: %s. Falling back to Demo Mode.", e)
            return None
    return None

def init_db():
    """Initializes the database. In demo mode or if Supabase is unavailable, sets up SQLite."""
    if settings.is_demo_mode:
        if settings.app_env == "prod":
            logger.warning("DEMO MODE ACTIVE IN PRODUCTION: Local disk data is non-persistent across restarts.")
        init_demo_db()
    else:
        sb = get_supabase_client()
        if not sb:
            logger.warning("Supabase connection failed. Falling back to local SQLite demo database.")
            init_demo_db()
