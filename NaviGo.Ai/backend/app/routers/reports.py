import uuid
import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.report import CreateReportRequest, VoteReportRequest, RoadReportResponse
from backend.app.db.repositories import RoadReportRepo
from backend.app.db.sqlite_demo import get_db_connection

router = APIRouter(prefix="/reports", tags=["Road Reports"])

def compute_time_ago(created_at_str: str) -> str:
    try:
        dt = datetime.datetime.fromisoformat(created_at_str)
        diff = (datetime.datetime.now() - dt).total_seconds()
        if diff < 120:
            return "Just now"
        elif diff < 3600:
            return f"{int(diff // 60)} min ago"
        elif diff < 86400:
            return f"{int(diff // 3600)} hours ago"
        else:
            return f"{int(diff // 86400)} days ago"
    except Exception:
        return "Recently reported"

@router.get("", response_model=List[RoadReportResponse])
async def list_road_reports(destination: Optional[str] = Query(None)):
    reports = RoadReportRepo.get_reports(destination_slug=destination)
    results = []
    for r in reports:
        tags = r.get("issue_tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = []

        summary = r.get("road_name")
        ai_info = r.get("ai_analysis_json")
        if isinstance(ai_info, str):
            try:
                ai_info = json.loads(ai_info)
                summary = ai_info.get("summary", summary)
            except Exception:
                pass
        elif isinstance(ai_info, dict):
            summary = ai_info.get("summary", summary)

        results.append(RoadReportResponse(
            id=r["id"],
            destination_slug=r["destination_slug"],
            road_name=r["road_name"],
            status=r["status"],
            issue_tags=tags,
            severity=r.get("severity", "medium"),
            confidence=r.get("confidence", 0.85),
            summary=summary,
            photo_url=r.get("photo_url"),
            latitude=r.get("latitude"),
            longitude=r.get("longitude"),
            confirmations_count=r.get("confirmations_count", 0),
            cleared_votes_count=r.get("cleared_votes_count", 0),
            is_authority_override=bool(r.get("is_authority_override", 0)),
            created_at=r.get("created_at", ""),
            time_ago=compute_time_ago(r.get("created_at", ""))
        ))
    return results

@router.post("", response_model=RoadReportResponse)
async def create_road_report(req: CreateReportRequest):
    report_id = f"rep-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO road_reports (id, user_id, destination_slug, road_name, status, issue_tags, severity, confidence, ai_analysis_json, photo_url, latitude, longitude, confirmations_count, cleared_votes_count, is_authority_override, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id, "demo-user-1", req.destination_slug, req.road_name, req.status,
        json.dumps(req.issue_tags), req.severity, req.confidence,
        json.dumps({"summary": req.summary or req.road_name, "disclaimer": "Community reported"}),
        req.photo_url or "", req.latitude or 34.9089, req.longitude or 73.6528, 1, 0, 0, now_iso
    ))

    # If severe issue (e.g. Landslide / Closed), fan out alert
    if req.severity in ["high", "severe"] or req.status == "closed":
        alert_id = f"alt-{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO alerts (id, destination_slug, title, description, alert_type, severity, source, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            alert_id, req.destination_slug, f"Urgent Road Alert: {req.road_name}",
            f"{req.summary or req.road_name} Reported status: {req.status.upper()}.",
            "road_closure" if req.status == "closed" else "traffic",
            "emergency" if req.severity == "severe" else "warning",
            "high_confidence_report", now_iso
        ))

    conn.commit()
    conn.close()

    return RoadReportResponse(
        id=report_id,
        destination_slug=req.destination_slug,
        road_name=req.road_name,
        status=req.status,
        issue_tags=req.issue_tags,
        severity=req.severity,
        confidence=req.confidence,
        summary=req.summary,
        photo_url=req.photo_url,
        latitude=req.latitude,
        longitude=req.longitude,
        confirmations_count=1,
        cleared_votes_count=0,
        is_authority_override=False,
        created_at=now_iso,
        time_ago="Just now"
    )

@router.post("/{report_id}/vote")
async def vote_road_report(report_id: str, vote: VoteReportRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    if vote.vote_type == "confirm":
        cursor.execute("UPDATE road_reports SET confirmations_count = confirmations_count + 1 WHERE id = ?", (report_id,))
    elif vote.vote_type == "cleared":
        cursor.execute("UPDATE road_reports SET cleared_votes_count = cleared_votes_count + 1 WHERE id = ?", (report_id,))

    conn.commit()
    cursor.execute("SELECT * FROM road_reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    d = dict(row)
    return {
        "id": d["id"],
        "confirmations": d["confirmations_count"],
        "cleared": d["cleared_votes_count"],
        "status": d["status"]
    }
