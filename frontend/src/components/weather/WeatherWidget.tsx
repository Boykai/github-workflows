/**
 * WeatherWidget component - displays current weather information
 */

import { useEffect, useState } from 'react';
import { weatherApi } from '@/services/api';
import type { Weather } from '@/types';
import './WeatherWidget.css';

export function WeatherWidget() {
  const [weather, setWeather] = useState<Weather | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchWeather = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await weatherApi.getCurrent();
      setWeather(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching weather:', err);
      setError('Unable to fetch weather data');
    } finally {
      setLoading(false);
    }
  };

  // Fetch weather on mount
  useEffect(() => {
    fetchWeather();
  }, []);

  const handleRefresh = () => {
    fetchWeather();
  };

  const getWeatherIcon = (iconCode: string) => {
    // Map OpenWeatherMap icon codes to emoji or text representations
    const iconMap: Record<string, string> = {
      '01d': '☀️', // clear sky day
      '01n': '🌙', // clear sky night
      '02d': '⛅', // few clouds day
      '02n': '☁️', // few clouds night
      '03d': '☁️', // scattered clouds
      '03n': '☁️',
      '04d': '☁️', // broken clouds
      '04n': '☁️',
      '09d': '🌧️', // shower rain
      '09n': '🌧️',
      '10d': '🌦️', // rain day
      '10n': '🌧️', // rain night
      '11d': '⛈️', // thunderstorm
      '11n': '⛈️',
      '13d': '❄️', // snow
      '13n': '❄️',
      '50d': '🌫️', // mist
      '50n': '🌫️',
    };
    
    return iconMap[iconCode] || '🌤️';
  };

  if (loading && !weather) {
    return (
      <div className="weather-widget" aria-live="polite" aria-busy="true">
        <div className="weather-loading">
          <div className="weather-spinner" role="status">
            <span className="sr-only">Loading weather...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error && !weather) {
    return (
      <div className="weather-widget weather-widget--error" role="alert">
        <span className="weather-error-icon" aria-hidden="true">⚠️</span>
        <span className="weather-error-text">{error}</span>
        <button 
          className="weather-refresh-btn"
          onClick={handleRefresh}
          aria-label="Retry fetching weather"
        >
          🔄
        </button>
      </div>
    );
  }

  if (!weather) {
    return null;
  }

  return (
    <div 
      className="weather-widget" 
      role="region" 
      aria-label="Current weather information"
      aria-live="polite"
    >
      <div className="weather-content">
        <div className="weather-icon" aria-hidden="true">
          {getWeatherIcon(weather.icon)}
        </div>
        
        <div className="weather-info">
          <div className="weather-temp">
            <span className="weather-temp-value">{Math.round(weather.temperature)}</span>
            <span className="weather-temp-unit">°C</span>
          </div>
          <div className="weather-description">
            {weather.description}
          </div>
        </div>

        <div className="weather-location">
          <span className="weather-location-icon" aria-hidden="true">📍</span>
          <span className="weather-location-text">{weather.location}</span>
        </div>

        <button
          className="weather-refresh-btn"
          onClick={handleRefresh}
          disabled={loading}
          aria-label="Refresh weather data"
          title="Refresh weather"
        >
          <span className={loading ? 'weather-refresh-icon--loading' : ''}>
            🔄
          </span>
        </button>
      </div>

      {weather.mock && (
        <div className="weather-mock-notice" role="note">
          <small>Demo data - Configure OPENWEATHER_API_KEY for live weather</small>
        </div>
      )}

      {lastUpdated && (
        <div className="weather-updated" role="status">
          <small>Updated: {lastUpdated.toLocaleTimeString()}</small>
        </div>
      )}
    </div>
  );
}
