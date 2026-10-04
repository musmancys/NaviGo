from fastapi import APIRouter
from datetime import datetime, timezone
from backend.app.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "demo_mode": settings.is_demo_mode,
        "ai_demo_mode": settings.is_ai_demo_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

@router.get("/config")
async def get_public_config():
    """
    Exposes only safe public configurations (Supabase URL, anon key, demo status).
    Never exposes service role keys or AI API keys.
    """
    return {
        "supabase_url": settings.supabase_url if not settings.is_demo_mode else "",
        "supabase_anon_key": settings.supabase_anon_key if not settings.is_demo_mode else "",
        "demo_mode": settings.is_demo_mode,
        "ai_demo_mode": settings.is_ai_demo_mode,
        "public_base_url": settings.public_base_url,
        "vapid_public_key": settings.vapid_public_key,
        "environment": settings.app_env
    }
