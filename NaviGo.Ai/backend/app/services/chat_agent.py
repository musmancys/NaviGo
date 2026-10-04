import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from backend.app.config import settings
from backend.app.services.tools import (
    tool_get_weather, tool_get_road_status, tool_search_places,
    tool_search_businesses, tool_estimate_budget
)
from backend.app.db.repositories import DestinationRepo, PlaceRepo

logger = logging.getLogger("navigo.services.chat")

SYSTEM_PROMPT = """You are NaviGo, a friendly AI travel companion for ALL of Pakistan — mountains, cities, coast, and heritage sites.

DESTINATIONS YOU COVER:
- 🏔️ North: Naran, Hunza, Skardu, Swat, Murree, Kashmir, Gilgit, Fairy Meadows
- 🏙️ Cities: Lahore, Karachi, Islamabad, Peshawar, Quetta, Multan, Faisalabad, Rawalpindi
- 🌊 Coastal: Gwadar, Ormara, Karachi beaches, Pasni
- 🏛️ Heritage: Lahore Fort, Badshahi Mosque, Mohenjo-daro, Taxila, Makli, Rohtas Fort

RULES:
1. Be warm, helpful, and conversational. Never dump raw data.
2. Use TOOL DATA provided to give accurate, grounded answers. If no tool data, use your own knowledge of Pakistan.
3. For budget questions, give a clear human-readable breakdown in PKR.
4. For city destinations (Lahore, Karachi etc.), cover food streets, heritage sites, shopping, nightlife (halal).
5. For coastal destinations, cover beaches, seafood, fishing villages.
6. For heritage sites, cover history, guided tours, visiting tips.
7. Never invent prices or places you aren't sure about — say "verify locally".
8. Match language: Urdu script → Urdu; Roman Urdu → Roman Urdu; English → English.
9. Keep responses concise — 3-5 sentences, then bullet points.
10. ALWAYS respond with JSON: {"text": "...", "cards": [{"emoji":"...","title":"...","subtitle":"..."}]}
"""

GREETING_WORDS = {"hello", "hi", "hey", "salam", "assalam", "helo", "hii", "sup", "yo", "howdy", "namaste", "aoa", "aap"}

# Budget intent: keywords OR PKR-range numbers (5000–5000000)
_PKR_PATTERN = re.compile(r'\b([5-9]\d{3}|\d{5,7})\b')

WEATHER_KWS  = ["weather", "mosam", "mausam", "rain", "barish", "thand", "snow", "temp", "temperature", "baarish", "garmi", "sardi"]
ROAD_KWS     = ["road", "rasta", "traffic", "landslide", "band", "pass", "open", "closed", "clear", "caution", "highway", "route", "blocked"]
BUDGET_KWS   = ["budget", "cost", "kharcha", "price", "pese", "rupees", "pkr", "rate", "cheap", "sasta", "kitna", "afford", "expensive", "mehnga", "trip cost", "how much"]
PLACES_KWS   = ["places", "visit", "jaghein", "attraction", "hotel", "restaurant", "things to do", "best places", "jana", "ghumna", "spots", "see", "explore"]

# Recommendation-mode triggers: user wants suggestions, no specific destination
RECOMMEND_KWS = [
    "somewhere", "any ideas", "any suggestion", "suggest", "recommend", "kahan jaun",
    "kahan jayein", "kahan jana", "where should", "where to go", "best place to go",
    "koi jagah", "koi destination", "acha jagah", "affordable", "within budget",
    "where can i go", "where can we go", "which place", "good place", "nice place",
    "pakistan mein", "pakistan me", "in pakistan with", "across pakistan",
    "got any ideas", "any recommendations", "low budget", "cheap trip"
]

# Standalone cities that can be origins but aren't in the destinations DB
_ORIGIN_CITIES = [
    "islamabad", "lahore", "karachi", "rawalpindi", "peshawar",
    "multan", "faisalabad", "sialkot", "quetta", "hyderabad",
    "sukkur", "gujranwala", "bahawalpur", "larkana", "abbottabad",
]


def _detect_destination_and_origin(msg_lower: str, default: str = "naran"):
    """
    Smart Urdu+English grammar parser:
      - 'Lahore se Naran jana hai' → dest=naran, origin=Lahore
      - 'Naran mein weather kaisa hai' → dest=naran, origin=Islamabad
      - 'karachi ke beaches' → dest=karachi
    Returns (destination_slug, origin_city_name)
    """
    from backend.app.db.repositories import DestinationRepo as _DR
    destinations = _DR.get_all()

    # Build list of (char_index, slug, matched_text) for all destination mentions
    mentions = []
    for d in destinations:
        name = d["name"].lower()
        slug = d["slug"]
        for text in [name, slug] if name != slug else [name]:
            idx = msg_lower.find(text)
            if idx >= 0:
                mentions.append((idx, slug, text))
                break

    mentions.sort(key=lambda x: x[0])

    # Mark mentions as ORIGIN if followed by " se" (Urdu: from)
    origin_slugs: set = set()
    origin_name: Optional[str] = None

    for idx, slug, text in mentions:
        after = msg_lower[idx + len(text): idx + len(text) + 6]
        if re.match(r'\s*se\b', after):
            origin_slugs.add(slug)
            if origin_name is None:
                origin_name = d["name"] if slug == d.get("slug") else text.title()

    # Also detect standalone cities (Lahore se, Karachi se, etc.) as origins
    for city in _ORIGIN_CITIES:
        idx = msg_lower.find(city)
        if idx >= 0:
            after = msg_lower[idx + len(city): idx + len(city) + 6]
            if re.match(r'\s*se\b', after) and origin_name is None:
                origin_name = city.title()

    # Also detect English "from X" pattern
    m = re.search(r'\bfrom\s+([a-z]+)', msg_lower)
    if m and origin_name is None:
        origin_name = m.group(1).title()

    # Pick destination = first mention NOT flagged as origin
    destination_slug: Optional[str] = None
    for idx, slug, text in mentions:
        if slug not in origin_slugs:
            destination_slug = slug
            break

    return destination_slug or default, origin_name or "Islamabad"


def _is_recommendation_query(msg_lower: str) -> bool:
    """Returns True when user wants destination suggestions (no specific place given)."""
    return any(kw in msg_lower for kw in RECOMMEND_KWS)


def _detect_destination(msg_lower: str, default: str = "naran") -> str:
    """Backwards-compatible single-value wrapper."""
    slug, _ = _detect_destination_and_origin(msg_lower, default)
    return slug


def _is_greeting(msg: str) -> bool:
    words = set(re.sub(r'[?!.,]', '', msg.lower()).split())
    return bool(words & GREETING_WORDS) and len(msg.split()) <= 5


def _detect_intents(msg_lower: str):
    is_weather = any(k in msg_lower for k in WEATHER_KWS)
    is_road    = any(k in msg_lower for k in ROAD_KWS)
    is_budget  = any(k in msg_lower for k in BUDGET_KWS) or bool(_PKR_PATTERN.search(msg_lower))
    is_places  = any(k in msg_lower for k in PLACES_KWS)
    return is_weather, is_road, is_budget, is_places


def _extract_budget_from_msg(msg_lower: str) -> Optional[int]:
    """Try to extract a PKR budget amount from the message."""
    m = _PKR_PATTERN.search(msg_lower)
    return int(m.group(0)) if m else None


def _detect_travelers(msg_lower: str) -> int:
    """Try to extract traveler count from message."""
    m = re.search(r'\b(\d+)\s*(?:people|persons?|log|banda|logon|travelers?)\b', msg_lower)
    if m:
        return max(1, min(int(m.group(1)), 20))
    # Roman Urdu pattern: "2 log" "3 log"
    m2 = re.search(r'\b(\d+)\s+log\b', msg_lower)
    if m2:
        return max(1, min(int(m2.group(1)), 20))
    return 4  # default


def _greeting_response() -> Dict[str, Any]:
    return {
        "text": (
            "Salam! 👋 I'm **NaviGo AI**, your travel companion for **all of Pakistan**.\n\n"
            "I cover every corner of the country:\n"
            "- 🏔️ **Northern Mountains** — Naran, Hunza, Skardu, Swat, Gilgit\n"
            "- 🏙️ **Major Cities** — Lahore, Karachi, Islamabad, Peshawar, Quetta\n"
            "- 🌊 **Coastal Pakistan** — Gwadar, Ormara, Clifton Beach\n"
            "- 🏛️ **Heritage Sites** — Badshahi Mosque, Mohenjo-daro, Lahore Fort, Taxila\n\n"
            "Ask me anything in **English, Urdu, or Roman Urdu**: budget, weather, road conditions, best places, or trip planning! 🤝"
        ),
        "cards": [
            {"emoji": "🏔️", "title": "Northern Pakistan", "subtitle": "Mountains & adventure"},
            {"emoji": "🏙️", "title": "Cities & Culture", "subtitle": "Lahore, Karachi, Islamabad"},
            {"emoji": "🌊", "title": "Coastal Pakistan", "subtitle": "Gwadar & Makran Coast"},
        ]
    }


async def _call_gemini_chat(user_message: str, tool_context: str, history: List[Dict]) -> Optional[Dict[str, Any]]:
    """Call Gemini API for conversational chat."""
    if not settings.gemini_api_key:
        return None

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )

    context_block = f"\n\nVERIFIED TOOL DATA — use this to answer accurately:\n{tool_context}" if tool_context else ""

    contents = []
    for turn in (history or [])[-6:]:
        role = "user" if turn.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": user_message + context_block}]})

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.5,
            "maxOutputTokens": 600
        }
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            res_json = resp.json()
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
        else:
            raise Exception(f"Gemini {resp.status_code}: {resp.text[:150]}")


async def _call_openai_chat(user_message: str, tool_context: str, history: List[Dict]) -> Optional[Dict[str, Any]]:
    """Call OpenAI ChatGPT for conversational chat."""
    if not settings.effective_openai_api_key:
        return None

    context_block = f"\n\nVERIFIED TOOL DATA:\n{tool_context}" if tool_context else ""

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\nRespond ONLY with valid JSON: {\"text\": \"...\", \"cards\": [...]}"}]
    for turn in (history or [])[-6:]:
        messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
    messages.append({"role": "user", "content": user_message + context_block})

    payload = {
        "model": settings.openai_model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.5,
        "max_tokens": 600
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.effective_openai_api_key}", "Content-Type": "application/json"},
            json=payload
        )
        if resp.status_code == 200:
            data = resp.json()
            return json.loads(data["choices"][0]["message"]["content"])
        else:
            raise Exception(f"OpenAI {resp.status_code}: {resp.text[:150]}")


def _build_recommendation_response(
    msg_lower: str, user_budget: Optional[int], travelers: int, history: List[Dict]
) -> Dict[str, Any]:
    """
    Returns destination recommendations when user asks 'somewhere in Pakistan',
    'kahan jaun', 'got any ideas', etc. Filters by budget if given.
    """
    from backend.app.db.sqlite_demo import get_db_connection

    # Get all destinations with price info
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT slug, name, sub_title, from_price_pkr, tags, best_season FROM destinations ORDER BY from_price_pkr ASC")
    all_dests = c.fetchall()
    conn.close()

    per_person_budget = (user_budget // travelers) if (user_budget and travelers > 0) else None

    # Filter by budget if given
    if per_person_budget:
        affordable = [d for d in all_dests if d[3] and d[3] <= per_person_budget * 1.4]
        if not affordable:
            affordable = all_dests[:6]  # always show something
    else:
        affordable = all_dests

    # Build response
    budget_line = f"**Rs. {user_budget:,} for {travelers} people** (Rs. {per_person_budget:,}/person):\n\n" if per_person_budget else "Here are some great destinations across Pakistan:\n\n"

    text = f"💡 **NaviGo Picks — {budget_line}"

    # Categorize
    shown = affordable[:8]
    for d in shown:
        slug, name, subtitle, price, tags_json, season = d
        tags = json.loads(tags_json) if tags_json else []
        tags_str = " • ".join(tags[:2]) if tags else ""
        text += f"- 📍 **{name}** — {subtitle[:60]}{'...' if len(subtitle) > 60 else ''}"
        if price:
            text += f" _(From Rs. {price:,})_"
        text += "\n"

    if per_person_budget and shown:
        cheapest = shown[0]
        text += f"\n✅ Most affordable: **{cheapest[1]}** starting from Rs. {cheapest[3]:,}"

    text += "\n\n_Ask me for full details, weather, or a trip plan for any of these!_"

    # Cards: top 3 picks
    cards = []
    for d in shown[:3]:
        slug, name, subtitle, price, tags_json, season = d
        tags = json.loads(tags_json) if tags_json else []
        emoji_map = {"Mountains": "🏔️", "Heritage": "🏛️", "Coastal": "🌊", "Beach": "🏖️",
                     "Culture": "🎭", "Nature": "🌲", "Hills": "⛰️", "Lakes": "💧",
                     "Adventure": "🧗", "Sufi": "⭐", "UNESCO": "🏛️", "Capital": "🏙️"}
        emoji = next((emoji_map[t] for t in tags if t in emoji_map), "📍")
        cards.append({
            "emoji": emoji,
            "title": name,
            "subtitle": f"From Rs. {price:,}" if price else subtitle[:35]
        })

    return {"text": text, "cards": cards}


async def _handle_general_query(user_message: str, history: List[Dict]) -> Dict[str, Any]:
    """
    Handles broad Pakistan questions with no specific destination:
    'Best time to visit Pakistan?', 'What food should I try?', etc.
    Calls Gemini/OpenAI directly with Pakistan-wide context.
    """
    pakistan_context = (
        "SCOPE: You are answering a general tourism question about Pakistan. "
        "Cover the whole country — north (Hunza, Skardu, Swat, Naran), "
        "cities (Lahore, Karachi, Islamabad, Peshawar), and coast (Gwadar). "
        "Do NOT focus on just one place unless the user asked about it."
    )

    if settings.gemini_api_key:
        try:
            result = await _call_gemini_chat(user_message, pakistan_context, history)
            if result and result.get("text"):
                return result
        except Exception as e:
            logger.warning("Gemini general query failed: %s", e)

    if settings.effective_openai_api_key:
        try:
            result = await _call_openai_chat(user_message, pakistan_context, history)
            if result and result.get("text"):
                return result
        except Exception as e:
            logger.warning("OpenAI general query failed: %s", e)

    # Deterministic fallback for general queries
    return {
        "text": (
            "Pakistan has incredible diversity across all regions! 🇵🇰\n\n"
            "- 🏔️ **Mountains & Adventure**: Hunza, Skardu, Naran, Swat, Fairy Meadows\n"
            "- 🏛️ **Heritage & Culture**: Lahore (Badshahi Mosque, Fort), Taxila (Gandhara), Mohenjo-daro\n"
            "- 🏙️ **City Life & Food**: Karachi (beaches, seafood), Islamabad (Margalla Hills), Peshawar (Namak Mandi)\n"
            "- 🌊 **Coastal Escapes**: Gwadar, Ormara, Makran Coastal Highway\n\n"
            "Tell me what kind of trip you want or ask about any specific destination!"
        ),
        "cards": [
            {"emoji": "🏔️", "title": "Northern Mountains", "subtitle": "Hunza, Skardu, Naran"},
            {"emoji": "🏛️", "title": "Heritage & Culture", "subtitle": "Lahore, Taxila, Multan"},
            {"emoji": "🌊", "title": "Coast & Beaches", "subtitle": "Gwadar & Karachi"},
        ]
    }


async def process_chat_message(
    user_message: str,
    destination_slug: Optional[str] = None,   # None = detect from message
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    AI chat for ALL of Pakistan.
    Flow:
    1. Greeting → instant response
    2. Recommendation query → destination picker with budget filter
    3. Destination detected → fetch tool data + call AI (grounded)
    4. No destination → pure AI (general Pakistan tourism question)
    """
    msg_lower = user_message.lower().strip()
    history = history or []

    # ── 1. Greeting ────────────────────────────────────────────────
    if _is_greeting(user_message):
        return _greeting_response()

    # ── 2. Recommendation mode ──────────────────────────────────────
    # "somewhere in Pakistan", "got any ideas", "kahan jaun", etc.
    all_dests = DestinationRepo.get_all()
    dest_names_in_msg = any(
        d["name"].lower() in msg_lower or d["slug"] in msg_lower
        for d in all_dests
    )
    if _is_recommendation_query(msg_lower) and not dest_names_in_msg:
        user_budget = _extract_budget_from_msg(msg_lower)
        travelers   = _detect_travelers(msg_lower)
        return _build_recommendation_response(msg_lower, user_budget, travelers, history)

    # ── 3. Detect destination from message (Urdu grammar aware) ─────
    active_dest, detected_origin = _detect_destination_and_origin(
        msg_lower, default=None  # None = no destination found
    )

    # Override with page context slug only if nothing detected from message
    if active_dest is None and destination_slug:
        active_dest = destination_slug

    is_weather, is_road, is_budget, is_places = _detect_intents(msg_lower)

    # ── 4. No destination + no specific tool intent → pure AI mode ──
    # Let Gemini answer general Pakistan tourism questions freely
    if active_dest is None and not any([is_weather, is_road, is_budget]):
        return await _handle_general_query(user_message, history)

    # If destination found but no specific intent, show places
    if not any([is_weather, is_road, is_budget, is_places]):
        is_places = True

    # ── 5. Pre-fetch grounded tool data ────────────────────────────
    tool_context_parts: List[str] = []
    cards: List[Dict] = []
    budget_data = None
    dest_label = (active_dest or "Pakistan").title()

    if is_weather and active_dest:
        try:
            w = await tool_get_weather(active_dest)
            tool_context_parts.append(
                f"WEATHER in {w.get('destination', dest_label)}: "
                f"{w.get('temp_c')}°C, {w.get('condition')}. "
                f"High {w.get('high_c')}°C / Low {w.get('low_c')}°C. "
                f"Wind {w.get('wind_kmh')} km/h. "
                f"Hazard: {w.get('hazard') or 'None'}."
            )
            cards = [
                {"emoji": "🌡️", "title": f"{w.get('temp_c')}°C", "subtitle": w.get("condition", "Current Temp")},
                {"emoji": "💨", "title": f"{w.get('wind_kmh')} km/h", "subtitle": "Wind Speed"},
                {"emoji": "🌤️", "title": f"High {w.get('high_c')}°C", "subtitle": f"Low {w.get('low_c')}°C"},
            ]
        except Exception as e:
            logger.warning("Weather tool failed: %s", e)

    if is_road and active_dest:
        try:
            r = await tool_get_road_status(active_dest)
            latest = r.get("latest_reports", [])
            latest_str = f"{latest[0]['road']} is {latest[0]['status']}" if latest else "No recent reports"
            tool_context_parts.append(
                f"ROAD STATUS for {r.get('destination', dest_label)}: {r.get('status', 'Open')}. "
                f"Community reports: {r.get('recent_reports_count', 0)}. "
                f"Latest: {latest_str}. "
                f"Active alerts: {', '.join(r.get('active_alerts', [])) or 'None'}."
            )
            if not cards:
                cards = [
                    {"emoji": "🚦", "title": f"Status: {r.get('status', 'Open')}", "subtitle": f"{dest_label} Routes"},
                    {"emoji": "📢", "title": f"{r.get('recent_reports_count', 0)} Reports", "subtitle": "Community Updates"},
                    {"emoji": "🛡️", "title": "Verify before travel", "subtitle": "Community data"},
                ]
        except Exception as e:
            logger.warning("Road tool failed: %s", e)

    if is_budget:
        try:
            user_budget = _extract_budget_from_msg(msg_lower)
            travelers   = _detect_travelers(msg_lower)
            dur_m = re.search(r'\b(\d+)\s*(?:din|day|days?|raat|night|nights?)\b', msg_lower)
            duration = max(1, min(int(dur_m.group(1)), 14)) if dur_m else 3

            b = tool_estimate_budget(duration_days=duration, travelers=travelers)
            budget_data = b
            bd = b.get("breakdown", {})
            total = b.get("total_estimated_pkr", 0)
            per_person = total // travelers if travelers > 0 else total

            budget_line = (
                f"BUDGET for {duration}-day trip to {dest_label} for {travelers} people: "
                f"Total ~Rs. {total:,} (Rs. {per_person:,}/person). "
                f"Transport: Rs. {bd.get('transport', 0):,}, "
                f"Hotel: Rs. {bd.get('hotel', 0):,}, "
                f"Food+Activities: Rs. {(bd.get('food', 0) + bd.get('activities', 0)):,}."
            )
            if user_budget:
                fits = "YES" if user_budget >= total else "NO — need more funds"
                budget_line += f" User budget Rs. {user_budget:,}: {fits}."
            tool_context_parts.append(budget_line)

            if not cards:
                cards = [
                    {"emoji": "🚗", "title": f"Rs. {bd.get('transport', 0):,}", "subtitle": "Transport"},
                    {"emoji": "🏨", "title": f"Rs. {bd.get('hotel', 0):,}", "subtitle": f"Hotel ({duration} nights)"},
                    {"emoji": "💰", "title": f"Rs. {total:,} total", "subtitle": f"Rs. {per_person:,}/person"},
                ]
        except Exception as e:
            logger.warning("Budget tool failed: %s", e)

    if is_places and active_dest:
        try:
            places = PlaceRepo.get_places(destination_slug=active_dest)
            if places:
                places_brief = "; ".join(
                    [f"{p['name']} ({p.get('place_type','attraction')}): {p.get('description','')[:55]}"
                     for p in places[:6]]
                )
                tool_context_parts.append(f"TOP PLACES in {dest_label}: {places_brief}.")
                if not cards:
                    top = places[:3]
                    cards = [
                        {"emoji": p.get("icon", "📍"), "title": p["name"],
                         "subtitle": p.get("description", f"In {dest_label}")[:40]}
                        for p in top
                    ]
            else:
                # No DB places for this destination → tell AI to use its own knowledge
                tool_context_parts.append(
                    f"No pre-seeded places for {dest_label} in database. "
                    f"Use your knowledge of real, well-known places in {dest_label}, Pakistan."
                )
        except Exception as e:
            logger.warning("Places tool failed: %s", e)

    tool_context = "\n".join(tool_context_parts)

    # ── 6. Try Gemini ───────────────────────────────────────────────
    if settings.gemini_api_key:
        try:
            result = await _call_gemini_chat(user_message, tool_context, history)
            if result and isinstance(result.get("text"), str) and result["text"].strip():
                if not result.get("cards"):
                    result["cards"] = cards
                return result
        except Exception as e:
            logger.warning("Gemini chat failed: %s", e)

    # ── 7. Try OpenAI ───────────────────────────────────────────────
    if settings.effective_openai_api_key:
        try:
            result = await _call_openai_chat(user_message, tool_context, history)
            if result and isinstance(result.get("text"), str) and result["text"].strip():
                if not result.get("cards"):
                    result["cards"] = cards
                return result
        except Exception as e:
            logger.warning("OpenAI chat failed: %s", e)

    # --- Smart deterministic fallback ---
    return _smart_fallback(msg_lower, active_dest, tool_context_parts, cards, budget_data,
                           _detect_travelers(msg_lower), _extract_budget_from_msg(msg_lower))


def _smart_fallback(
    msg_lower: str, active_dest: str,
    tool_parts: List[str], cards: List[Dict],
    budget_data: Optional[Dict], travelers: int, user_budget: Optional[int]
) -> Dict[str, Any]:
    """Produce a clean, human-readable response from tool data — no raw dumps."""
    dest = active_dest.title()
    is_weather, is_road, is_budget, is_places = _detect_intents(msg_lower)

    # Budget response
    if is_budget and budget_data:
        bd = budget_data.get("breakdown", {})
        total = budget_data.get("total_estimated_pkr", 0)
        dur_m = re.search(r'\b(\d+)\s*(?:din|day|days?)\b', msg_lower)
        duration = int(dur_m.group(1)) if dur_m else 3
        per_person = total // travelers if travelers > 0 else total

        text = f"💰 **Budget Estimate for {dest}** ({duration} days, {travelers} people):\n\n"
        text += f"- 🚗 Transport: **Rs. {bd.get('transport', 0):,}**\n"
        text += f"- 🏨 Hotel ({duration} nights): **Rs. {bd.get('hotel', 0):,}**\n"
        text += f"- 🍽️ Food + Activities: **Rs. {(bd.get('food', 0) + bd.get('activities', 0)):,}**\n"
        text += f"- 📊 **Total: Rs. {total:,}** (Rs. {per_person:,}/person)\n"

        if user_budget:
            if user_budget >= total:
                text += f"\n✅ Your budget of **Rs. {user_budget:,}** is sufficient!"
            else:
                shortfall = total - user_budget
                text += f"\n⚠️ Your budget of **Rs. {user_budget:,}** is short by Rs. {shortfall:,}. Consider reducing hotel nights or sharing transport."
        return {"text": text, "cards": cards}

    # Weather response
    if is_weather and tool_parts:
        for part in tool_parts:
            if "WEATHER" in part:
                # Parse values cleanly
                text = f"🌤️ **Weather in {dest}**\n\n{part.replace('WEATHER in ', '').replace(f'{dest}: ', '')}"
                return {"text": text, "cards": cards}

    # Road response
    if is_road and tool_parts:
        for part in tool_parts:
            if "ROAD STATUS" in part:
                text = f"🛣️ **Road Conditions — {dest}**\n\n"
                text += part.replace("ROAD STATUS for ", "").replace(f"{dest}: ", "") + "\n\n"
                text += "_⚠️ Always verify road status locally before travelling._"
                return {"text": text, "cards": cards}

    # Places response
    if is_places and tool_parts:
        for part in tool_parts:
            if "TOP PLACES" in part:
                places_raw = part.replace(f"TOP PLACES in {dest}: ", "").rstrip(".")
                items = places_raw.split("; ")
                text = f"📍 **Top Places to Visit in {dest}**\n\n"
                for item in items[:5]:
                    if ":" in item:
                        name, desc = item.split(":", 1)
                        text += f"- **{name.strip()}**: {desc.strip()}\n"
                return {"text": text, "cards": cards}

    # Generic fallback
    text = (
        f"I'm NaviGo AI, your guide for **all of Pakistan**! 🇵🇰\n\n"
        f"Ask me about **{dest}** or any destination across Pakistan:\n"
        f"- *\"Best places to visit in Lahore?\"*\n"
        f"- *\"What's the weather in Hunza?\"*\n"
        f"- *\"Is Babusar Pass road open?\"*\n"
        f"- *\"40,000 mein 3 din ka Naran trip ho sakta hai?\"*\n"
        f"- *\"Top things to do in Karachi?\"*"
    )
    if not cards:
        cards = [
            {"emoji": "🏔️", "title": "North Pakistan", "subtitle": "Mountains & valleys"},
            {"emoji": "🏙️", "title": "Cities & Culture", "subtitle": "Lahore, Karachi, Islamabad"},
            {"emoji": "🌊", "title": "Coastal Pakistan", "subtitle": "Gwadar & Makran"},
        ]
    return {"text": text, "cards": cards}
