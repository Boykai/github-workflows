"""Weather API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.services.weather import get_weather_service

logger = logging.getLogger(__name__)
router = APIRouter()


class WeatherResponse(BaseModel):
    """Weather data response model."""
    temperature: float
    condition: str
    description: str
    icon: str
    location: str
    humidity: int
    wind_speed: float
    timestamp: int | None = None
    mock: bool = False


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    city: Annotated[str | None, Query(description="City name")] = None,
    country: Annotated[str | None, Query(description="Country code")] = None,
) -> WeatherResponse:
    """
    Get current weather data for a location.
    
    If no location is provided, defaults to San Francisco, US.
    If OpenWeatherMap API key is not configured, returns mock data.
    """
    weather_service = get_weather_service()
    
    try:
        weather_data = await weather_service.get_current_weather(city=city, country=country)
        return WeatherResponse(**weather_data)
    except Exception as e:
        logger.error("Error fetching weather: %s", e)
        # Return fallback weather data
        return WeatherResponse(
            temperature=18.0,
            condition="Unknown",
            description="Weather data unavailable",
            icon="01d",
            location=f"{city or 'San Francisco'}, {country or 'US'}",
            humidity=50,
            wind_speed=0.0,
            timestamp=None,
            mock=True
        )
