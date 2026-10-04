import logging
from typing import Optional, Dict, Any
from fastapi import Header, Depends
from backend.app.config import settings
from backend.app.errors import UnauthorizedException
from backend.app.db.client import get_supabase_client
from backend.app.db.sqlite_demo import get_db_connection

logger = logging.getLogger("navigo.deps")

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validates Supabase JWT if configured, or falls back to demo tourist profile.
    """
    if not authorization or not authorization.startswith("Bearer "):
        # Return default Demo user if unauthenticated or in Demo Mode
        return {
            "id": "demo-user-1",
            "email": "traveler@navigo.pk",
            "name": "Traveler",
            "role": "tourist"
        }

    token = authorization.split(" ")[1]
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.auth.get_user(token)
            if res and res.user:
                return {
                    "id": res.user.id,
                    "email": res.user.email,
                    "name": res.user.user_metadata.get("full_name", res.user.email.split("@")[0]),
                    "role": res.user.user_metadata.get("role", "tourist")
                }
        except Exception as e:
            logger.warning("Supabase token verification failed: %s", e)
            raise UnauthorizedException("Invalid authentication token")

    # In demo mode, simulate user from token or return demo user
    return {
        "id": "demo-user-1",
        "email": "traveler@navigo.pk",
        "name": "Traveler",
        "role": "tourist"
    }

def get_db():
    """Returns database connection or client depending on mode."""
    if settings.is_demo_mode:
        conn = get_db_connection()
        try:
            yield conn
        finally:
            conn.close()
    else:
        sb = get_supabase_client()
        if sb:
            yield sb
        else:
            conn = get_db_connection()
            try:
                yield conn
            finally:
                conn.close()
