import json
import base64
import logging
from typing import List, Dict, Any
import httpx
from backend.app.config import settings
from backend.app.schemas.trip import TripPlanRequest, DayPlan, TripStop

logger = logging.getLogger("navigo.services.llm.openai")

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

def _get_headers() -> Dict[str, str]:
    api_key = settings.effective_openai_api_key
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

async def call_openai_planner(
    req: TripPlanRequest,
    dest_name: str,
    places: List[Dict[str, Any]],
    weather: Dict[str, Any],
    warnings: List[str]
) -> List[DayPlan]:
    """
    ChatGPT / OpenAI Fallback Trip Planner
    """
    places_str = "\n".join([f"- {p['name']} ({p['place_type']}): {p.get('description', '')}" for p in places[:15]])
    warnings_str = "\n".join([f"- {w}" for w in warnings]) if warnings else "None"

    system_prompt = (
        "You are NaviGo's expert Northern Pakistan travel planning AI. "
        "Create a realistic itinerary based on provided verified places and safety conditions. "
        "Always respond with a JSON object containing a 'days' array."
    )

    user_prompt = f"""
Create a realistic {req.duration_days}-day itinerary for {dest_name}, starting from {req.origin}.
Travelers: {req.travelers_count}, Interests: {', '.join(req.interests)}, Transport: {req.transport_type}.

Current Weather: {weather.get('temp')}°C, {weather.get('cond')}.
Safety & Road Alerts:
{warnings_str}

AVAILABLE VERIFIED PLACES (You MUST use places from this list):
{places_str}

Respond STRICTLY with valid JSON following this format:
{{
  "days": [
    {{
      "day_number": 1,
      "day_badge": "DAY 01",
      "theme": "Arrival & Exploration",
      "stops": [
        {{ "place_name": "Naran Bazaar", "activity": "Check-in and local food", "time_of_day": "Morning" }}
      ],
      "notes": "Advice for high altitude and warm layers"
    }}
  ]
}}
"""

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.4
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(OPENAI_CHAT_URL, headers=_get_headers(), json=payload)
        if resp.status_code == 200:
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_text)
            days_list = parsed.get("days", parsed)
            if isinstance(days_list, dict):
                days_list = [days_list]
            return [DayPlan(**d) for d in days_list]
        else:
            raise Exception(f"OpenAI API returned status {resp.status_code}: {resp.text[:200]}")

async def call_openai_vision(image_bytes: bytes, disclaimer: str) -> Dict[str, Any]:
    """
    ChatGPT / OpenAI Multimodal Vision for Road Hazard Inspection
    """
    b64_img = base64.b64encode(image_bytes).decode('utf-8')

    system_prompt = (
        "You are NaviGo's Road Hazard Inspector for Northern Pakistan mountain highways. "
        "Examine the road photo for hazards (Mud, Standing Water, Snow Coverage, Landslide, Boulder Fall, Road Damage, Washout, Blockage, or Clear). "
        "STRICT SAFETY RULE: Vision results are supporting evidence, never guarantees. Never output 'road is safe'. "
        "Respond STRICTLY in valid JSON."
    )

    user_content = [
        {
            "type": "text",
            "text": """
Respond in JSON with this schema:
{
  "is_road_photo": true,
  "issues": ["Mud", "Standing Water"],
  "severity": "medium",
  "confidence": 0.89,
  "summary": "Possible mud and standing water detected.",
  "suggested_status": "caution"
}
"""
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64_img}"
            }
        }
    ]

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(OPENAI_CHAT_URL, headers=_get_headers(), json=payload)
        if resp.status_code == 200:
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_text)
            parsed["disclaimer"] = disclaimer
            return parsed
        else:
            raise Exception(f"OpenAI Vision API returned status {resp.status_code}: {resp.text[:200]}")

async def call_openai_review_summary(reviews_text: str, count: int, business_id: str) -> Dict[str, Any]:
    """
    ChatGPT / OpenAI Review Summarizer
    """
    system_prompt = (
        "You are NaviGo's Tourism Review Summarizer. "
        "Summarize tourist reviews for a Northern Pakistan business into concise pros and cons in JSON."
    )

    user_prompt = f"""
REVIEWS:
{reviews_text}

Respond strictly in valid JSON:
{{
  "pros": ["Clean rooms", "Good location"],
  "cons": ["Weak Wi-Fi"],
  "based_on_count": {count}
}}
"""

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(OPENAI_CHAT_URL, headers=_get_headers(), json=payload)
        if resp.status_code == 200:
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            res = json.loads(raw)
            res["based_on_count"] = count
            return res
        else:
            raise Exception(f"OpenAI API returned status {resp.status_code}: {resp.text[:200]}")
