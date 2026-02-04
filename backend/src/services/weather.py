"""Weather service for fetching current weather data."""

import logging
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""
    
    # Using OpenWeatherMap as it's free and reliable
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    # Default location (San Francisco) if geolocation not available
    DEFAULT_CITY = "San Francisco"
    DEFAULT_COUNTRY = "US"
    
    def __init__(self, api_key: str | None = None):
        """Initialize weather service with optional API key."""
        self.api_key = api_key
        
    async def get_current_weather(self, city: str | None = None, country: str | None = None) -> Dict[str, Any]:
        """
        Fetch current weather data for a given location.
        
        Args:
            city: City name (optional, defaults to San Francisco)
            country: Country code (optional, defaults to US)
            
        Returns:
            Dictionary containing weather data:
            - temperature: Current temperature in Celsius
            - condition: Weather condition (e.g., "Clouds", "Clear", "Rain")
            - description: Detailed description
            - icon: Weather icon code
            - location: City and country
            - humidity: Humidity percentage
            - wind_speed: Wind speed in m/s
            
        Raises:
            Exception: If weather data cannot be fetched
        """
        # Use defaults if not provided
        city = city or self.DEFAULT_CITY
        country = country or self.DEFAULT_COUNTRY
        
        # If no API key, return mock data for demo purposes
        if not self.api_key:
            logger.warning("No weather API key configured, returning mock data")
            return self._get_mock_weather(city, country)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "q": f"{city},{country}",
                    "appid": self.api_key,
                    "units": "metric"  # Use Celsius
                }
                
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "temperature": round(data["main"]["temp"], 1),
                    "condition": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "icon": data["weather"][0]["icon"],
                    "location": f"{data['name']}, {data['sys']['country']}",
                    "humidity": data["main"]["humidity"],
                    "wind_speed": round(data["wind"]["speed"], 1),
                    "timestamp": data["dt"]
                }
                
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching weather: %s", e)
            if e.response.status_code == 401:
                # Invalid API key, return mock data
                return self._get_mock_weather(city, country)
            elif e.response.status_code == 404:
                # City not found, return default
                return self._get_mock_weather(self.DEFAULT_CITY, self.DEFAULT_COUNTRY)
            raise Exception(f"Failed to fetch weather data: {e}")
        except httpx.RequestError as e:
            logger.error("Request error fetching weather: %s", e)
            raise Exception(f"Failed to fetch weather data: {e}")
        except Exception as e:
            logger.error("Unexpected error fetching weather: %s", e)
            raise Exception(f"Failed to fetch weather data: {e}")
    
    def _get_mock_weather(self, city: str, country: str) -> Dict[str, Any]:
        """Return mock weather data for demo/fallback purposes."""
        return {
            "temperature": 18.5,
            "condition": "Clouds",
            "description": "partly cloudy",
            "icon": "02d",
            "location": f"{city}, {country}",
            "humidity": 65,
            "wind_speed": 3.5,
            "timestamp": None,
            "mock": True
        }


# Global weather service instance
_weather_service: WeatherService | None = None


def get_weather_service() -> WeatherService:
    """Get or create global weather service instance."""
    global _weather_service
    if _weather_service is None:
        from src.config import get_settings
        settings = get_settings()
        # Get API key from settings (to be added)
        api_key = getattr(settings, "openweather_api_key", None)
        _weather_service = WeatherService(api_key=api_key)
    return _weather_service
