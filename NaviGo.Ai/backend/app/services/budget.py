import math
from typing import Dict, Any, List, Optional
from backend.app.db.sqlite_demo import get_db_connection

def get_price_catalog_map() -> Dict[str, int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_key, base_price_pkr FROM price_catalog")
    rows = cursor.fetchall()
    conn.close()
    return {r["item_key"]: r["base_price_pkr"] for r in rows}

def calculate_trip_budget(
    duration_days: int,
    travelers_count: int,
    target_budget_pkr: int,
    transport_type: str = "car",
    hotel_tier: str = "standard"
) -> Dict[str, Any]:
    prices = get_price_catalog_map()

    # Fallback default prices if catalog is empty
    car_daily = prices.get("transport_car_daily", 7000)
    van_daily = prices.get("transport_van_daily", 12000)
    bus_ticket = prices.get("transport_bus_seat", 2800)
    hotel_standard = prices.get("hotel_standard_night", 8500)
    food_daily = prices.get("food_standard_daily", 1600)
    activity_base = prices.get("jeep_local_safari", 6000)

    # 1. Transport Calculation
    transport_type = transport_type.lower()
    if transport_type == "van":
        transport_cost = van_daily * duration_days
    elif transport_type == "bus":
        transport_cost = bus_ticket * travelers_count * 2 # return ticket
    elif transport_type == "bike":
        num_bikes = math.ceil(travelers_count / 2)
        transport_cost = num_bikes * 3000 * duration_days
    else: # Car
        transport_cost = car_daily * duration_days

    # 2. Hotel Calculation (2 people per room)
    nights = max(1, duration_days - 1)
    rooms_needed = math.ceil(travelers_count / 2)
    room_rate = hotel_standard
    if hotel_tier == "budget":
        room_rate = prices.get("hotel_budget_night", 4500)
    elif hotel_tier == "luxury":
        room_rate = prices.get("hotel_luxury_night", 18000)
    hotel_cost = rooms_needed * nights * room_rate

    # 3. Food Calculation
    food_cost = travelers_count * duration_days * food_daily

    # 4. Activities & Jeeps
    jeeps_needed = math.ceil(travelers_count / 6)
    activities_cost = jeeps_needed * activity_base + (travelers_count * 500 * duration_days)

    # 5. Contingency buffer
    subtotal = transport_cost + hotel_cost + food_cost + activities_cost
    contingency = math.ceil(subtotal * 0.05)
    total_cost = subtotal + contingency

    # 6. Budget Status & Analysis
    diff = target_budget_pkr - total_cost
    status = "Within Budget"
    status_class = "within"
    tips = []

    if diff >= 0:
        status = "Within Budget"
        status_class = "within"
        tips.append("Your allocated budget comfortably covers this itinerary.")
    elif abs(diff) <= target_budget_pkr * 0.15:
        status = "Close to Budget"
        status_class = "close"
        tips.append("Consider booking guest houses or shared jeeps to save Rs. 4,000–6,000.")
    else:
        status = "Over Budget"
        status_class = "over"
        tips.append(f"Estimated cost exceeds budget by Rs. {abs(diff):,}.")
        tips.append("Tip: Use public transport or choose budget hotels to lower costs.")

    return {
        "target_budget_pkr": target_budget_pkr,
        "total_estimated_pkr": total_cost,
        "difference_pkr": diff,
        "status": status,
        "status_class": status_class,
        "breakdown": {
            "transport": transport_cost,
            "hotel": hotel_cost,
            "food": food_cost,
            "activities": activities_cost,
            "contingency": contingency
        },
        "tips": tips
    }
