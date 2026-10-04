import uuid
import datetime
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Header, HTTPException, status
from backend.app.config import settings
from backend.app.db.repositories import DestinationRepo
from backend.app.services.weather import get_destination_weather
from backend.app.db.sqlite_demo import get_db_connection

logger = logging.getLogger("navigo.cron")

router = APIRouter(prefix="/internal/cron", tags=["Internal Cron"])

@router.post("/weather-alerts")
async def run_weather_alerts_cron(authorization: str = Header(None)):
    """
    Scheduled job endpoint to check weather hazards across all Pakistan destinations.
    Protected by CRON_SECRET header to ensure safe cloud & Replit operation.
    """
    expected_secret = f"Bearer {settings.cron_secret}"
    if not authorization or authorization != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing CRON_SECRET bearer token."
        )

    destinations = DestinationRepo.get_all()
    alerts_generated = []
    conn = get_db_connection()
    cursor = conn.cursor()

    for dest in destinations:
        try:
            weather = await get_destination_weather(dest["latitude"], dest["longitude"])
            hazard = weather.get("hazard")
            if hazard:
                alert_id = f"cron-alt-{uuid.uuid4().hex[:8]}"
                now_iso = datetime.datetime.now().isoformat()
                title = f"Automated Weather Alert: {dest['name']}"
                desc = f"{hazard} (Current: {weather['temp']}°C, {weather['cond']}, Wind: {weather['wind_kmh']} km/h)."

                cursor.execute("""
                INSERT INTO alerts (id, destination_slug, title, description, alert_type, severity, source, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    alert_id, dest["slug"], title, desc,
                    "weather_warning", "warning", "ai_weather_cron", now_iso
                ))
                alerts_generated.append({"destination": dest["name"], "hazard": hazard})
        except Exception as e:
            logger.warning("Weather check failed for %s: %s", dest.get("slug"), e)

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "checked_destinations_count": len(destinations),
        "alerts_generated_count": len(alerts_generated),
        "alerts": alerts_generated,
        "timestamp": datetime.datetime.now().isoformat()
    }
