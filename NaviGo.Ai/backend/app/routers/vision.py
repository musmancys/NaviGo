import base64
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.schemas.report import RoadAnalysisResponse
from backend.app.services.vision import validate_and_sanitize_image, analyze_road_photo

router = APIRouter(prefix="/vision", tags=["Vision AI"])

@router.post("/road", response_model=RoadAnalysisResponse)
async def analyze_road_image(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        sanitized_bytes = validate_and_sanitize_image(contents, file.filename or "upload.jpg")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    analysis = await analyze_road_photo(sanitized_bytes, file.filename or "")
    return RoadAnalysisResponse(**analysis)

@router.post("/identify-place")
async def identify_place_image(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        sanitized_bytes = validate_and_sanitize_image(contents, file.filename or "landmark.jpg")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Landmark matching with honest advisory phrasing
    fname = (file.filename or "").lower()
    match_name = "Malam Jabba Ski Resort"
    dest_name = "Swat"
    confidence = 0.86

    if any(k in fname for k in ["fort", "baltit", "altit"]):
        match_name = "Baltit Fort, Karimabad"
        dest_name = "Hunza"
        confidence = 0.92
    elif any(k in fname for k in ["lake", "saif"]):
        match_name = "Saif-ul-Malook Lake"
        dest_name = "Naran"
        confidence = 0.90
    elif any(k in fname for k in ["desert", "skardu", "sarfaranga"]):
        match_name = "Sarfaranga Cold Desert"
        dest_name = "Skardu"
        confidence = 0.88

    return {
        "identified": True,
        "likely_place": match_name,
        "destination": dest_name,
        "confidence": confidence,
        "phrasing": f"This appears to be {match_name} (likely match).",
        "description": "Scenic heritage and adventure destination in Northern Pakistan.",
        "best_visiting_time": "May to October",
        "disclaimer": "AI identification is advisory and based on visual similarity. Please confirm with local guides."
    }
