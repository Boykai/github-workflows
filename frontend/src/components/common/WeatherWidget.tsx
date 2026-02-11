/**
 * Weather widget component for displaying current weather information.
 */

import { useState } from 'react';
import { useWeather } from '@/hooks/useWeather';
import { getWeatherIconUrl } from '@/services/weather';
import './WeatherWidget.css';

export function WeatherWidget() {
  const { weather, isLoading, error, manualCity, setManualCity, clearError } = useWeather();
  const [showCityInput, setShowCityInput] = useState(false);
  const [cityInput, setCityInput] = useState('');

  const handleCitySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (cityInput.trim()) {
      setManualCity(cityInput.trim());
      setShowCityInput(false);
      setCityInput('');
      clearError();
    }
  };

  const handleChangeLocation = () => {
    setShowCityInput(true);
    setCityInput(manualCity);
  };

  // Show loading state
  if (isLoading && !weather) {
    return (
      <div className="weather-widget">
        <div className="weather-loading">
          <div className="weather-spinner" />
          <span>Loading weather...</span>
        </div>
      </div>
    );
  }

  // Show error state with city input
  if (error && !weather) {
    return (
      <div className="weather-widget weather-error">
        <div className="weather-error-content">
          <span className="weather-error-icon">⚠️</span>
          <span className="weather-error-message">{error.message}</span>
        </div>
        {!showCityInput ? (
          <button 
            className="weather-city-btn"
            onClick={() => setShowCityInput(true)}
          >
            Enter City
          </button>
        ) : (
          <form className="weather-city-form" onSubmit={handleCitySubmit}>
            <input
              type="text"
              className="weather-city-input"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              placeholder="Enter city name..."
              autoFocus
            />
            <button type="submit" className="weather-city-submit">
              ✓
            </button>
            <button 
              type="button" 
              className="weather-city-cancel"
              onClick={() => {
                setShowCityInput(false);
                setCityInput('');
              }}
            >
              ✕
            </button>
          </form>
        )}
      </div>
    );
  }

  // Show weather data
  if (weather) {
    return (
      <div className="weather-widget">
        {showCityInput ? (
          <form className="weather-city-form" onSubmit={handleCitySubmit}>
            <input
              type="text"
              className="weather-city-input"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              placeholder="Enter city name..."
              autoFocus
            />
            <button type="submit" className="weather-city-submit">
              ✓
            </button>
            <button 
              type="button" 
              className="weather-city-cancel"
              onClick={() => {
                setShowCityInput(false);
                setCityInput('');
              }}
            >
              ✕
            </button>
          </form>
        ) : (
          <>
            <div className="weather-content">
              <img 
                src={getWeatherIconUrl(weather.icon)}
                alt={weather.condition}
                className="weather-icon"
              />
              <div className="weather-info">
                <div className="weather-temp">{weather.temperature}°C</div>
                <div className="weather-condition">{weather.condition}</div>
              </div>
            </div>
            <div className="weather-location">
              <span className="weather-location-text">{weather.location}</span>
              <button 
                className="weather-change-btn"
                onClick={handleChangeLocation}
                aria-label="Change location"
                title="Change location"
              >
                📍
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  return null;
}
