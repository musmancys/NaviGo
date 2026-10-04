import json
import asyncio
import uuid
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.app.db.repositories import AlertRepo
from backend.app.db.sqlite_demo import get_db_connection

router = APIRouter(prefix="/alerts", tags=["Travel Alerts"])

class AlertResponse(BaseModel):
    id: str
    destination_slug: Optional[str] = None
    title: str
    description: str
    alert_type: str
    severity: str
    source: str
    is_active: bool
    created_at: str

class CreateAlertRequest(BaseModel):
    destination_slug: Optional[str] = None
    title: str
    description: str
    alert_type: str = "warning"
    severity: str = "warning"
    source: str = "authority"

class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: Dict[str, str]

# In-memory storage for push subscriptions
_PUSH_SUBSCRIPTIONS = []

@router.get("", response_model=List[AlertResponse])
async def list_active_alerts(destination: Optional[str] = Query(None)):
    alerts = AlertRepo.get_active(destination_slug=destination)
    return [
        AlertResponse(
            id=a["id"],
            destination_slug=a.get("destination_slug"),
            title=a["title"],
            description=a["description"],
            alert_type=a["alert_type"],
            severity=a["severity"],
            source=a["source"],
            is_active=bool(a.get("is_active", 1)),
            created_at=a.get("created_at", "")
        )
        for a in alerts
    ]

@router.get("/stream")
async def stream_live_alerts():
    """
    SSE stream with 15-second heartbeat comments for proxy survival on cloud/Replit.
    """
    async def alert_event_generator():
        last_count = -1
        while True:
            alerts = AlertRepo.get_active()
            if len(alerts) != last_count:
                last_count = len(alerts)
                data = [
                    {
                        "id": a["id"],
                        "destination_slug": a.get("destination_slug"),
                        "title": a["title"],
                        "description": a["description"],
                        "severity": a["severity"],
                        "alert_type": a["alert_type"]
                    }
                    for a in alerts
                ]
                yield f"event: alerts\ndata: {json.dumps(data)}\n\n"

            # Heartbeat comment to keep hosted proxy connections alive
            yield ": heartbeat\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(
        alert_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("", response_model=AlertResponse)
async def create_alert(req: CreateAlertRequest):
    alert_id = f"alt-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO alerts (id, destination_slug, title, description, alert_type, severity, source, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        alert_id, req.destination_slug, req.title, req.description,
        req.alert_type, req.severity, req.source, now_iso
    ))
    conn.commit()
    conn.close()

    return AlertResponse(
        id=alert_id,
        destination_slug=req.destination_slug,
        title=req.title,
        description=req.description,
        alert_type=req.alert_type,
        severity=req.severity,
        source=req.source,
        is_active=True,
        created_at=now_iso
    )

@router.post("/subscribe")
async def subscribe_push_notifications(sub: PushSubscriptionRequest):
    _PUSH_SUBSCRIPTIONS.append(sub.model_dump())
    return {"success": True, "message": "Subscribed to travel alerts push notifications."}
