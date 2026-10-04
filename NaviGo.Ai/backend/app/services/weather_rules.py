import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("navigo.services.weather_rules")

def evaluate_activity_safety(
    activity_name: str,
    place_name: str,
    weather: Dict[str, Any],
    road_reports: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Returns (is_safe, hazard_reason, recommended_alternative).
    Deterministic rules without LLM arithmetic.
    """
    act_lower = (activity_name + " " + place_name).lower()
    temp = weather.get("temp", 15)
    precip_prob = weather.get("precip_probability", 0)
    cond = weather.get("cond", "").lower()

    # Rule 1: High mountain pass in adverse weather (e.g. Babusar Top, Deosai)
    if any(k in act_lower for k in ["babusar", "deosai", "pass", "top", "4173m"]):
        if temp < 2 or "snow" in cond:
            return (
                False,
                f"Sub-zero conditions / snow risk ({temp}°C) at high elevation pass.",
                "Visit lower valley spots (e.g. Kaghan Valley, Naran Bazaar, Trout Hatchery) and cross pass during midday if open."
            )
        if any(r.get("status") == "closed" for r in road_reports if "babusar" in r.get("road_name", "").lower()):
            return (
                False,
                "Babusar Pass road closed due to landslide/blockage.",
                "Explore Saif-ul-Malook Lake or local valleys instead."
            )

    # Rule 2: Remote alpine lake / jeep track in heavy rain (e.g. Mahodand, Saif-ul-Malook)
    if any(k in act_lower for k in ["mahodand", "lake", "boating", "ushush"]):
        if precip_prob > 60 or "heavy rain" in cond or "thunderstorm" in cond:
            return (
                False,
                f"Heavy rain expected ({precip_prob}% chance). Steep dirt jeep tracks become hazardous.",
                "Swap outdoor lake visit to cultural sites (e.g. Swat Museum, Fizagat Park, Mingora Handicrafts)."
            )

    # Rule 3: Ski slope / outdoor chairlift in storm
    if any(k in act_lower for k in ["ski", "chairlift", "zipline", "malam jabba"]):
        if weather.get("wind_kmh", 10) > 45 or "thunderstorm" in cond:
            return (
                False,
                f"High winds ({weather.get('wind_kmh')} km/h) make chairlifts unsafe.",
                "Visit indoor resort lounge, local dining, or nearby heritage sites."
            )

    return (True, None, None)
