from fastapi import APIRouter, HTTPException
from backend.app.schemas.weather import WeatherForecastResponse
from backend.app.db.repositories import DestinationRepo
from backend.app.services.weather import get_destination_weather

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/{slug}", response_model=WeatherForecastResponse)
async def get_weather_by_slug(slug: str):
    dest = DestinationRepo.get_by_slug(slug)
    if not dest:
        raise HTTPException(status_code=404, detail=f"Destination '{slug}' not found")

    weather = await get_destination_weather(dest["latitude"], dest["longitude"])
    return weather
