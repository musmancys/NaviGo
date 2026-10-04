import re
import json
import base64
import logging
from typing import Dict, Any, List, Optional
from backend.app.config import settings

logger = logging.getLogger("navigo.services.voice")

URDU_NUM_WORDS = {
    "aik": 1, "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4,
    "paanch": 5, "panch": 5, "che": 6, "saat": 7, "aath": 8, "nau": 9,
    "dus": 10, "das": 10, "pandrah": 15, "bees": 20, "tees": 30,
    "chalees": 40, "pachas": 50, "pachaas": 50, "saath": 60, "sattar": 70,
    "assi": 80, "nabbay": 90, "sau": 100, "so": 100
}

CITIES = ["Islamabad", "Lahore", "Karachi", "Rawalpindi", "Peshawar", "Multan", "Faisalabad", "Sialkot", "Quetta", "Gujranwala", "Hyderabad", "Sukkur", "Larkana", "Bahawalpur"]
DESTINATIONS = {
    # Northern mountains
    "naran": ["naran", "kaghan", "saif ul malook", "babusar"],
    "hunza": ["hunza", "karimabad", "attabad", "passu"],
    "skardu": ["skardu", "shangrila", "kachura", "deosai"],
    "swat": ["swat", "malam jabba", "kalam", "bahrain"],
    "murree": ["murree", "patriata", "mall road", "nathia gali"],
    "kashmir": ["kashmir", "neelum", "muzaffarabad", "rawalakot"],
    "gilgit": ["gilgit", "naltar"],
    "fairy": ["fairy meadows", "fairy", "nanga parbat"],
    # Major cities
    "lahore": ["lahore", "lahore fort", "badshahi", "anarkali", "food street", "data darbar"],
    "karachi": ["karachi", "clifton", "sea view", "do darya", "saddar", "defence"],
    "islamabad": ["islamabad", "faisal mosque", "margalla", "f-7", "blue area"],
    "peshawar": ["peshawar", "qissa khwani", "deans", "smugglers bazaar"],
    "quetta": ["quetta", "hanna lake", "urak valley", "ziarat"],
    "multan": ["multan", "shah rukn-e-alam", "qasim bagh"],
    "faisalabad": ["faisalabad", "lyallpur", "ghanta ghar"],
    # Coastal
    "gwadar": ["gwadar", "hammerhead", "padi zirr", "makran"],
    "ormara": ["ormara", "ormara beach"],
    # Heritage sites
    "mohenjo-daro": ["mohenjo daro", "mohenjo-daro", "indus valley"],
    "taxila": ["taxila", "sirkap", "jaulian"],
    "makli": ["makli", "thatta", "shah jahan mosque"],
}

def parse_urdu_numerals_and_budget(text: str) -> Optional[int]:
    """
    Parses phrases like '40 hazar', '40,000', '35 hazar', '1 lakh', 'pachaas hazar'.
    """
    text_lower = text.lower()

    # Match direct digits with hazar/lakh (e.g. 40 hazar, 40k)
    m1 = re.search(r'(\d+)\s*(?:hazar|hzaar|k)\b', text_lower)
    if m1:
        return int(m1.group(1)) * 1000

    m2 = re.search(r'(\d+)\s*(?:lakh|lac)\b', text_lower)
    if m2:
        return int(m2.group(1)) * 100000

    # Match numeric amounts like 35000 or Rs. 40,000
    m3 = re.search(r'(?:rs\.?|rupees|pkr)?\s*(\d{1,3}(?:,\d{3})+|\d{4,6})', text_lower)
    if m3:
        clean = m3.group(1).replace(',', '')
        val = int(clean)
        if val >= 5000:
            return val

    # Match verbal words like 'chalees hazar', 'bees hazar'
    for word, num in URDU_NUM_WORDS.items():
        if f"{word} hazar" in text_lower:
            return num * 1000

    return None

def parse_voice_transcript_heuristics(transcript: str) -> Dict[str, Any]:
    text = transcript.lower()

    # ── Origin detection: "X se" = from X ──────────────────────────
    # Pattern 1: destination name followed by "se"
    origin = "Islamabad"
    for city in CITIES:
        idx = text.find(city.lower())
        if idx >= 0:
            after = text[idx + len(city): idx + len(city) + 6]
            if re.match(r'\s*se\b', after):
                origin = city
                break

    # Pattern 2: English "from X"
    m_from = re.search(r'\bfrom\s+([a-z]+)', text)
    if m_from and origin == "Islamabad":
        matched = m_from.group(1).title()
        if matched in CITIES:
            origin = matched

    # Pattern 3: fallback scan any city mentioned even without "se"
    if origin == "Islamabad":
        for city in CITIES:
            if city.lower() in text and city != "Islamabad":
                origin = city
                break

    # ── Destination detection: pick slug NOT marked as origin ────────
    # First, find which slugs appear before "se" (these are origins)
    origin_slugs = set()
    for slug, keywords in DESTINATIONS.items():
        for kw in keywords:
            idx = text.find(kw)
            if idx >= 0:
                after = text[idx + len(kw): idx + len(kw) + 6]
                if re.match(r'\s*se\b', after):
                    origin_slugs.add(slug)

    # Now pick destination = first slug matched that is NOT an origin
    detected_dest = None
    # Scan in order of appearance in the text
    slug_appearances = []
    for slug, keywords in DESTINATIONS.items():
        for kw in keywords:
            idx = text.find(kw)
            if idx >= 0:
                slug_appearances.append((idx, slug))
                break

    slug_appearances.sort(key=lambda x: x[0])
    for _, slug in slug_appearances:
        if slug not in origin_slugs:
            detected_dest = slug
            break

    if detected_dest is None:
        detected_dest = "naran"  # absolute fallback

    # Duration detection ('3 din', '5 days', '3 days')
    duration = 3
    dur_match = re.search(r'(\d+)\s*(?:din|days?|roz)\b', text)
    if dur_match:
        duration = int(dur_match.group(1))
    else:
        for word, val in URDU_NUM_WORDS.items():
            if f"{word} din" in text or f"{word} days" in text:
                duration = val
                break

    # Travelers count ('4 log', '4 people', '2 bande')
    travelers = 4
    trav_match = re.search(r'(\d+)\s*(?:log|people|person|persons|bande|afraad|dost)\b', text)
    if trav_match:
        travelers = int(trav_match.group(1))

    # Budget
    budget = parse_urdu_numerals_and_budget(text) or 35000

    # Interests
    interests = []
    if any(k in text for k in ["nature", "pahad", "qudrat", "mountains"]):
        interests.append("nature")
    if any(k in text for k in ["adventure", "trekking", "hiking"]):
        interests.append("adventure")
    if any(k in text for k in ["khana", "food", "trout", "taste"]):
        interests.append("food")
    if any(k in text for k in ["tasweer", "photo", "camera"]):
        interests.append("photography")

    # Missing fields determination
    missing = []
    if not any(k in text for keywords in DESTINATIONS.values() for k in keywords):
        missing.append("destination")
    if not (dur_match or any(f"{w} din" in text for w in URDU_NUM_WORDS)):
        missing.append("duration")

    return {
        "transcript": transcript,
        "language": "roman_urdu" if any(w in text for w in ["mujhe", "jana", "hai", "hazar", "din"]) else "english",
        "params": {
            "origin": origin,
            "destination": detected_dest,
            "duration_days": duration,
            "budget_pkr": budget,
            "travelers": travelers,
            "interests": interests or ["nature", "adventure"]
        },
        "missing_fields": missing
    }

async def parse_audio_voice_input(audio_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Calls Gemini API with audio file or falls back to standard heuristics.
    """
    if settings.gemini_api_key and not settings.is_ai_demo_mode:
        try:
            return await call_gemini_audio(audio_bytes)
        except Exception as e:
            logger.warning("Gemini audio transcription failed (%s). Using heuristic parser.", e)

    # Demo fallback sample transcription
    demo_transcript = "Mujhe Lahore se 3 din ke liye Naran jana hai, budget 40 hazar hai"
    return parse_voice_transcript_heuristics(demo_transcript)

async def call_gemini_audio(audio_bytes: bytes) -> Dict[str, Any]:
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')

    prompt = """
Listen to this audio recording of a traveler planning a trip in Pakistan (in Urdu, Roman Urdu, or English).
1. Transcribe the audio verbatim.
2. Extract the trip parameters:
   - origin (starting city, e.g. Lahore, Islamabad, Karachi, Peshawar)
   - destination (any Pakistan destination: Naran, Hunza, Skardu, Lahore, Karachi, Islamabad, Gwadar, Peshawar, Quetta, Murree, Taxila, Mohenjo-daro, etc.)
   - duration_days (integer)
   - budget_pkr (integer, normalize Urdu numerals e.g. '40 hazar' -> 40000, '1 lakh' -> 100000)
   - travelers (integer, default 4)
   - interests (array of strings: nature, adventure, food, culture, photography, relaxation, history, beach)

Respond strictly in valid JSON:
{
  "transcript": "...",
  "language": "roman_urdu",
  "params": {
    "origin": "Lahore",
    "destination": "naran",
    "duration_days": 3,
    "budget_pkr": 40000,
    "travelers": 4,
    "interests": ["nature", "adventure"]
  },
  "missing_fields": []
}
"""
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": "audio/mp3",
                        "data": b64_audio
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
            raw = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw)
        else:
            raise Exception(f"Gemini Audio API returned status {resp.status_code}")
