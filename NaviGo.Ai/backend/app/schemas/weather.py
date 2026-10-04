from typing import Optional
from pydantic import BaseModel, Field

class WeatherForecastResponse(BaseModel):
    source: str = Field(description="Data provider: open-meteo or estimate")
    temp: int = Field(description="Current temperature in Celsius")
    feels_like: int = Field(description="Apparent temperature")
    cond: str = Field(description="Condition description")
    icon: str = Field(description="Weather emoji icon")
    high: int = Field(description="Daily high in Celsius")
    low: int = Field(description="Daily low in Celsius")
    humidity: int = Field(description="Relative humidity percentage")
    wind_kmh: int = Field(description="Wind speed in km/h")
    precip_probability: Optional[int] = Field(default=0, description="Precipitation probability %")
    hazard: Optional[str] = Field(default=None, description="Advisory safety warning if adverse weather")
    is_cached: bool = Field(default=False)
    updated_at: str
