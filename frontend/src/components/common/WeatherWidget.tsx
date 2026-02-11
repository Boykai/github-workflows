/**
 * WeatherWidget component displays current weather information.
 * Shows temperature, weather condition, and icon.
 * Supports location-based weather and manual city entry.
 */

import { useState } from 'react';
import { useWeather } from '@/hooks/useWeather';
import { getWeatherIconUrl } from '@/services/weather';
import './WeatherWidget.css';

export function WeatherWidget() {
  const {
    weather,
    isLoading,
    error,
    locationDenied,
    manualCity,
    fetchWeatherByCity,
    refresh,
  } = useWeather();

  const [showCityInput, setShowCityInput] = useState(false);
  const [cityInput, setCityInput] = useState('');

  const handleCitySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cityInput.trim()) {
      await fetchWeatherByCity(cityInput.trim());
      setShowCityInput(false);
      setCityInput('');
    }
  };

  if (isLoading && !weather) {
    return (
      <div className="weather-widget" role="status" aria-label="Loading weather">
        <div className="weather-loading">
          <div className="weather-spinner" />
          <span className="sr-only">Loading weather...</span>
        </div>
      </div>
    );
  }

  if (error && !weather) {
    return (
      <div className="weather-widget weather-error">
        <button
          className="weather-city-btn"
          onClick={() => setShowCityInput(!showCityInput)}
          aria-label="Enter city for weather"
          title="Enter city"
        >
          🌍
        </button>
        {showCityInput && (
          <form onSubmit={handleCitySubmit} className="weather-city-form">
            <input
              type="text"
              placeholder="Enter city..."
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              className="weather-city-input"
              aria-label="City name"
              autoFocus
            />
            <button type="submit" className="weather-city-submit" aria-label="Search">
              →
            </button>
          </form>
        )}
      </div>
    );
  }

  if (!weather) {
    return null;
  }

  return (
    <div className="weather-widget" role="region" aria-label="Current weather">
      <button
        className="weather-content"
        onClick={refresh}
        aria-label={`Current weather in ${weather.city}: ${weather.temperature}°C, ${weather.description}. Click to refresh`}
        title="Click to refresh"
      >
        <img
          src={getWeatherIconUrl(weather.icon)}
          alt={weather.description}
          className="weather-icon"
        />
        <div className="weather-info">
          <div className="weather-temp">
            {weather.temperature}°C
          </div>
          <div className="weather-city">
            {weather.city}
          </div>
        </div>
      </button>

      {(locationDenied || manualCity) && (
        <button
          className="weather-city-btn"
          onClick={() => setShowCityInput(!showCityInput)}
          aria-label="Change city"
          title="Change city"
        >
          🌍
        </button>
      )}

      {showCityInput && (
        <form onSubmit={handleCitySubmit} className="weather-city-form">
          <input
            type="text"
            placeholder="Enter city..."
            value={cityInput}
            onChange={(e) => setCityInput(e.target.value)}
            className="weather-city-input"
            aria-label="City name"
            autoFocus
          />
          <button type="submit" className="weather-city-submit" aria-label="Search">
            →
          </button>
        </form>
      )}
    </div>
  );
}
