"""Tests for weather service."""

import pytest
from src.services.weather import WeatherService


@pytest.mark.asyncio
async def test_weather_service_returns_mock_data_without_api_key():
    """Test that weather service returns mock data when no API key is configured."""
    service = WeatherService(api_key=None)
    weather = await service.get_current_weather()
    
    assert weather is not None
    assert weather['mock'] is True
    assert 'temperature' in weather
    assert 'condition' in weather
    assert 'location' in weather
    assert 'icon' in weather


@pytest.mark.asyncio
async def test_weather_service_mock_data_has_required_fields():
    """Test that mock weather data has all required fields."""
    service = WeatherService(api_key=None)
    weather = await service.get_current_weather()
    
    required_fields = [
        'temperature', 'condition', 'description', 'icon',
        'location', 'humidity', 'wind_speed', 'timestamp', 'mock'
    ]
    
    for field in required_fields:
        assert field in weather, f"Missing required field: {field}"


@pytest.mark.asyncio
async def test_weather_service_uses_default_location():
    """Test that weather service uses default location when not specified."""
    service = WeatherService(api_key=None)
    weather = await service.get_current_weather()
    
    assert 'San Francisco' in weather['location']
    assert 'US' in weather['location']


@pytest.mark.asyncio
async def test_weather_service_custom_location():
    """Test that weather service accepts custom location."""
    service = WeatherService(api_key=None)
    weather = await service.get_current_weather(city="New York", country="US")
    
    assert 'New York' in weather['location']
    assert 'US' in weather['location']
