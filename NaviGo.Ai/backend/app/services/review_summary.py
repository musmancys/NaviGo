import json
import logging
from typing import List, Dict, Any, Optional
from backend.app.config import settings

logger = logging.getLogger("navigo.services.reviews")

# Cache summaries: business_id -> { "pros": [], "cons": [], "based_on_count": int }
_SUMMARY_CACHE: Dict[str, Dict[str, Any]] = {}

async def summarize_reviews(business_id: str, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not reviews:
        return {
            "pros": ["No reviews yet"],
            "cons": [],
            "based_on_count": 0
        }

    # Check cache if review count hasn't changed
    if business_id in _SUMMARY_CACHE and _SUMMARY_CACHE[business_id].get("based_on_count") == len(reviews):
        return _SUMMARY_CACHE[business_id]

    review_texts = [f"- Rating {r.get('rating', 5)}/5: {r.get('comment', '')}" for r in reviews]
    formatted_reviews = "\n".join(review_texts)

    if settings.gemini_api_key and not settings.is_ai_demo_mode:
        try:
            return await call_gemini_review_summary(formatted_reviews, len(reviews), business_id)
        except Exception as e:
            logger.warning("Gemini review summary failed (%s). Checking OpenAI fallback.", e)
            if settings.effective_openai_api_key:
                try:
                    from backend.app.services.llm.openai import call_openai_review_summary
                    res = await call_openai_review_summary(formatted_reviews, len(reviews), business_id)
                    _SUMMARY_CACHE[business_id] = res
                    return res
                except Exception as oe:
                    logger.warning("OpenAI review summary failed (%s). Using fallback extractor.", oe)
    elif settings.effective_openai_api_key:
        try:
            from backend.app.services.llm.openai import call_openai_review_summary
            res = await call_openai_review_summary(formatted_reviews, len(reviews), business_id)
            _SUMMARY_CACHE[business_id] = res
            return res
        except Exception as e:
            logger.warning("OpenAI review summary failed (%s). Using fallback extractor.", e)

    # Heuristic review analyzer based on real text content
    pros = []
    cons = []

    full_corpus = " ".join([r.get("comment", "").lower() for r in reviews])

    if any(k in full_corpus for k in ["clean", "saaf", "fresh", "neat"]):
        pros.append("Clean, tidy, and well-maintained rooms")
    if any(k in full_corpus for k in ["view", "scenery", "nazara", "location", "lake"]):
        pros.append("Excellent scenic location and mountain views")
    if any(k in full_corpus for k in ["helpful", "kind", "staff", "hospitality", "friendly"]):
        pros.append("Polite and hospitable local hosts")
    if any(k in full_corpus for k in ["food", "breakfast", "khana", "trout"]):
        pros.append("Delicious hot food and local cuisine")

    if any(k in full_corpus for k in ["wifi", "internet", "signal", "slow"]):
        cons.append("Weak Wi-Fi signal in high mountain terrain")
    if any(k in full_corpus for k in ["parking", "narrow", "car"]):
        cons.append("Limited vehicle parking space during peak weekends")
    if any(k in full_corpus for k in ["hot water", "cold", "heater", "gyser"]):
        cons.append("Intermittent hot water during morning rush")

    if not pros:
        pros.append("Good value for money and polite service")
    if not cons:
        cons.append("Remote location requires extra travel preparation")

    result = {
        "pros": pros[:3],
        "cons": cons[:2],
        "based_on_count": len(reviews)
    }

    _SUMMARY_CACHE[business_id] = result
    return result

async def call_gemini_review_summary(reviews_text: str, count: int, business_id: str) -> Dict[str, Any]:
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"

    prompt = f"""
You are NaviGo's Tourism Review Summarizer for Pakistan.
Analyze the following tourist reviews for a Pakistani hospitality or tourism business.
Summarize ONLY what is explicitly mentioned in these reviews into concise pros and cons.

REVIEWS:
{reviews_text}

Respond strictly in valid JSON:
{{
  "pros": ["Clean rooms", "Good location", "Helpful staff"],
  "cons": ["Weak Wi-Fi", "Limited parking"],
  "based_on_count": {count}
}}
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            res_json = resp.json()
            raw = res_json["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(raw)
            data["based_on_count"] = count
            _SUMMARY_CACHE[business_id] = data
            return data
        else:
            raise Exception(f"Gemini API returned status {resp.status_code}")
