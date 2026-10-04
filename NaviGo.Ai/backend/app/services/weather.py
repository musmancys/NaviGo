import time
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("navigo.services.weather")

# 30-minute in-memory cache: (lat_round, lng_round) -> { "data": ..., "expires_at": ... }
_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 1800 # 30 minutes

WEATHER_CODE_MAP = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Slight snow fall", "🌨️"),
    73: ("Moderate snow fall", "❄️"),
    75: ("Heavy snow fall", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️")
}

def map_weather_code(code: int):
    return WEATHER_CODE_MAP.get(code, ("Partly cloudy", "⛅"))

async def get_destination_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}"
    now = time.time()

    if cache_key in _WEATHER_CACHE:
        cached = _WEATHER_CACHE[cache_key]
        if cached["expires_at"] > now:
            return cached["data"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
        "timezone": "Asia/Karachi"
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                daily = data.get("daily", {})

                w_code = current.get("weather_code", 2)
                cond_text, cond_icon = map_weather_code(w_code)

                high_temp = daily.get("temperature_2m_max", [current.get("temperature_2m", 18)])[0]
                low_temp = daily.get("temperature_2m_min", [current.get("temperature_2m", 12)])[0]
                precip_prob = daily.get("precipitation_probability_max", [0])[0]

                # Assess weather safety hazard
                hazard = None
                if w_code in [71, 73, 75, 85, 86]:
                    hazard = "Snowfall hazard — mountain passes may become slippery or closed"
                elif w_code in [65, 82, 95, 96, 99]:
                    hazard = "Heavy rain / thunderstorm — watch for flash floods and mudslides"
                elif current.get("temperature_2m", 10) < 0:
                    hazard = "Sub-zero temperatures — black ice risk on high-altitude roads"

                result = {
                    "source": "open-meteo",
                    "temp": round(current.get("temperature_2m", 18)),
                    "feels_like": round(current.get("apparent_temperature", 18)),
                    "cond": cond_text,
                    "icon": cond_icon,
                    "high": round(high_temp),
                    "low": round(low_temp),
                    "humidity": current.get("relative_humidity_2m", 55),
                    "wind_kmh": round(current.get("wind_speed_10m", 10)),
                    "precip_probability": precip_prob,
                    "hazard": hazard,
                    "is_cached": False,
                    "updated_at": "Just now"
                }

                _WEATHER_CACHE[cache_key] = {
                    "data": {**result, "is_cached": True},
                    "expires_at": now + CACHE_TTL_SECONDS
                }
                return result
    except Exception as e:
        logger.warning("Open-Meteo request failed (%s). Returning seasonal estimation.", e)

    # Realistic Northern Pakistan fallback if network fails
    fallback = {
        "source": "seasonal_estimate",
        "temp": 18,
        "feels_like": 17,
        "cond": "Partly Cloudy",
        "icon": "⛅",
        "high": 21,
        "low": 12,
        "humidity": 55,
        "wind_kmh": 12,
        "precip_probability": 15,
        "hazard": None,
        "is_cached": False,
        "updated_at": "Estimated (offline)"
    }
    return fallback
