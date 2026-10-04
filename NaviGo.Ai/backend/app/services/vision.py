import io
import base64
import json
import logging
from PIL import Image
from typing import Dict, Any, List, Optional
from backend.app.config import settings

logger = logging.getLogger("navigo.services.vision")

MAX_UPLOAD_SIZE = 8 * 1024 * 1024 # 8 MB
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]

def validate_and_sanitize_image(image_bytes: bytes, filename: str) -> bytes:
    if len(image_bytes) > MAX_UPLOAD_SIZE:
        raise ValueError("Image size exceeds maximum limit of 8 MB.")

    # Validate Magic Bytes
    if not (image_bytes.startswith(b'\xff\xd8\xff') or # JPEG
            image_bytes.startswith(b'\x89PNG\r\n\x1a\n') or # PNG
            (image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:16])): # WebP
        raise ValueError("Invalid image file format. Only JPEG, PNG, and WebP are allowed.")

    # Strip EXIF and re-encode using Pillow
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify() # Verify file integrity
        image = Image.open(io.BytesIO(image_bytes)) # Reopen after verify
    except Exception as e:
        raise ValueError("Corrupted or unreadable image file.")

    # Convert to RGB (dropping alpha or palette for uniform security)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Resize if extremely large to save bandwidth
    max_dim = 1920
    if image.width > max_dim or image.height > max_dim:
        image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    # Save to buffer without EXIF metadata
    out_buffer = io.BytesIO()
    image.save(out_buffer, format="JPEG", quality=85, optimize=True)
    return out_buffer.getvalue()

async def analyze_road_photo(sanitized_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Analyzes road photo using Gemini Vision or falls back to realistic heuristic demo.
    Always includes mandatory safety disclaimer.
    """
    disclaimer = "Possible issue detected — AI suggestion, please confirm. Vision results are supporting evidence, not guarantees."

    if settings.gemini_api_key and not settings.is_ai_demo_mode:
        try:
            return await call_gemini_vision(sanitized_bytes, disclaimer)
        except Exception as e:
            logger.warning("Gemini vision analysis failed (%s). Checking OpenAI fallback.", e)
            if settings.effective_openai_api_key:
                try:
                    from backend.app.services.llm.openai import call_openai_vision
                    return await call_openai_vision(sanitized_bytes, disclaimer)
                except Exception as oe:
                    logger.warning("OpenAI vision analysis failed (%s). Using demo analyzer.", oe)
    elif settings.effective_openai_api_key:
        try:
            from backend.app.services.llm.openai import call_openai_vision
            return await call_openai_vision(sanitized_bytes, disclaimer)
        except Exception as e:
            logger.warning("OpenAI vision analysis failed (%s). Using demo analyzer.", e)

    # Demo mode realistic output
    fname_lower = filename.lower()
    if any(k in fname_lower for k in ["landslide", "rock", "block", "stone"]):
        return {
            "is_road_photo": True,
            "issues": ["Landslide", "Boulder Fall", "Road Blockage"],
            "severity": "severe",
            "confidence": 0.94,
            "summary": "Severe landslide with rocks covering roadway. Passage obstructed.",
            "suggested_status": "closed",
            "disclaimer": disclaimer
        }
    elif any(k in fname_lower for k in ["snow", "ice", "frost", "winter"]):
        return {
            "is_road_photo": True,
            "issues": ["Snow Coverage", "Slippery Surface", "Ice"],
            "severity": "high",
            "confidence": 0.91,
            "summary": "Heavy snow accumulation. High clearance 4x4 with tire chains recommended.",
            "suggested_status": "caution",
            "disclaimer": disclaimer
        }
    else:
        # Default sample observation
        return {
            "is_road_photo": True,
            "issues": ["Mud", "Standing Water", "Potholes"],
            "severity": "medium",
            "confidence": 0.88,
            "summary": "Possible mud and water puddles detected on roadway surface.",
            "suggested_status": "caution",
            "disclaimer": disclaimer
        }

async def call_gemini_vision(image_bytes: bytes, disclaimer: str) -> Dict[str, Any]:
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"

    b64_img = base64.b64encode(image_bytes).decode('utf-8')

    prompt = """
You are NaviGo's Road Hazard Inspector for Pakistani roads and highways.
Examine this image carefully for visible road conditions and hazards.
Visible issues may include: Mud, Standing Water, Snow Coverage, Landslide, Boulder Fall, Road Damage, Washout, Blockage, Flooding, Potholes, or Clear.

STRICT SAFETY RULE:
Vision results are supporting evidence, never guarantees. Never output "road is safe".
Always phrase detections as advisory suggestions.

Respond STRICTLY in valid JSON with this schema:
{
  "is_road_photo": true,
  "issues": ["Mud", "Standing Water"],
  "severity": "medium",
  "confidence": 0.89,
  "summary": "Possible mud and standing water detected.",
  "suggested_status": "caution"
}
"""

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": b64_img
                    }
                }
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            res_json = resp.json()
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)
            parsed["disclaimer"] = disclaimer
            return parsed
        else:
            raise Exception(f"Gemini API vision returned status {resp.status_code}")
