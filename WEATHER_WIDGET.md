# Weather Widget Implementation

## Overview
This implementation adds a weather widget to the GitHub Projects Chat Interface that displays current weather information in the app header.

## Features Implemented

### Backend
- **Weather Service** (`backend/src/services/weather.py`)
  - Fetches weather data from OpenWeatherMap API
  - Falls back to mock data if API key is not configured
  - Supports custom location (city, country)
  - Default location: San Francisco, US

- **Weather API Endpoint** (`backend/src/api/weather.py`)
  - `GET /api/v1/weather/current` - Returns current weather data
  - Query parameters: `city` (optional), `country` (optional)
  - Returns: temperature, condition, description, icon, location, humidity, wind_speed

### Frontend
- **WeatherWidget Component** (`frontend/src/components/weather/WeatherWidget.tsx`)
  - Displays current weather with temperature, icon, and location
  - Auto-refreshes on app launch
  - Manual refresh button with loading state
  - Error handling with fallback UI
  - Full accessibility support:
    - ARIA labels and roles
    - Keyboard navigation
    - Screen reader compatible
    - Loading/error states announced

- **Styling** (`frontend/src/components/weather/WeatherWidget.css`)
  - Matches app's existing design theme
  - Responsive design (mobile-friendly)
  - High contrast mode support
  - Reduced motion support
  - Clean, modern appearance

### Configuration
- Added `OPENWEATHER_API_KEY` to configuration
- Updated `.env.example` with weather API key documentation
- Updated `docker-compose.yml` to pass API key to backend

## Weather Data

### With API Key
When `OPENWEATHER_API_KEY` is configured, the widget fetches live weather data from OpenWeatherMap.

### Without API Key (Demo Mode)
When no API key is configured, the widget displays mock weather data:
- Temperature: 18.5°C
- Condition: Clouds (partly cloudy)
- Location: San Francisco, US
- Displays a notice: "Demo data - Configure OPENWEATHER_API_KEY for live weather"

## UI Placement
The weather widget is placed in the app header between the app title and the login button:
```
[GitHub Projects Chat]  [Weather Widget]  [Login/User]
```

## Example API Response
```json
{
  "temperature": 18.5,
  "condition": "Clouds",
  "description": "partly cloudy",
  "icon": "02d",
  "location": "San Francisco, US",
  "humidity": 65,
  "wind_speed": 3.5,
  "timestamp": null,
  "mock": true
}
```

## Weather Icons
The widget uses emoji weather icons:
- ☀️ Clear sky (day)
- 🌙 Clear sky (night)
- ⛅ Few clouds (day)
- ☁️ Cloudy
- 🌧️ Rain
- 🌦️ Rain (day)
- ⛈️ Thunderstorm
- ❄️ Snow
- 🌫️ Mist/Fog
- 🌤️ Default

## Tests

### Backend Tests (`backend/tests/test_weather.py`)
- ✅ Returns mock data without API key
- ✅ Mock data has all required fields
- ✅ Uses default location when not specified
- ✅ Accepts custom location

### Frontend Tests (`frontend/src/components/weather/WeatherWidget.test.tsx`)
- ✅ Shows loading state initially
- ✅ Displays weather data when loaded
- ✅ Displays error state when API fails
- ✅ Displays mock data notice when mock flag is true
- ✅ Has proper accessibility attributes

## Setup Instructions

### 1. Get OpenWeatherMap API Key (Optional)
1. Go to https://openweathermap.org/api
2. Sign up for a free account
3. Generate an API key
4. Add to `.env`: `OPENWEATHER_API_KEY=your_api_key_here`

### 2. Without API Key
The widget will work without an API key, displaying mock weather data with a notice.

## Technical Details

### Dependencies
- Backend: `httpx` (already in dependencies)
- Frontend: React hooks (useState, useEffect)

### Error Handling
- Network errors: Displays error message with retry button
- Invalid API key: Falls back to mock data
- City not found: Falls back to default location
- Timeout: 10 second request timeout

### Accessibility
- Proper ARIA roles: `region`, `alert`, `status`
- ARIA labels for all interactive elements
- Keyboard navigation support
- Screen reader announcements for state changes
- High contrast mode support
- Reduced motion support for animations

## Future Enhancements
- Location detection using browser geolocation API
- User preferences for temperature units (Celsius/Fahrenheit)
- Extended forecast (3-day, 7-day)
- Weather alerts and warnings
- Multiple location support
- Customizable widget position
