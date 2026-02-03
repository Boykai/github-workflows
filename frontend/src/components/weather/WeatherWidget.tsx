/**
 * Weather widget component
 * Displays current weather information with location search
 */

import { useState, useRef, useEffect } from 'react';
import { useWeather } from '@/hooks/useWeather';
import { getWeatherIconUrl } from '@/services/weather';
import './WeatherWidget.css';

export function WeatherWidget() {
  const { weather, isLoading, error, refreshWeather, setLocation } = useWeather();
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchInput, setSearchInput] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const widgetRef = useRef<HTMLDivElement>(null);

  // Close expanded view when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (widgetRef.current && !widgetRef.current.contains(event.target as Node)) {
        setIsExpanded(false);
      }
    }

    if (isExpanded) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isExpanded]);

  const handleLocationSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;

    setIsSearching(true);
    try {
      await setLocation(searchInput.trim());
      setSearchInput('');
      setIsExpanded(false);
    } catch (err) {
      // Error is handled by the hook
    } finally {
      setIsSearching(false);
    }
  };

  const getWeatherIcon = (condition: string): string => {
    switch (condition.toLowerCase()) {
      case 'clear':
        return '☀️';
      case 'clouds':
        return '☁️';
      case 'rain':
      case 'drizzle':
        return '🌧️';
      case 'thunderstorm':
        return '⛈️';
      case 'snow':
        return '❄️';
      case 'mist':
      case 'fog':
        return '🌫️';
      default:
        return '🌤️';
    }
  };

  if (error && !weather) {
    return (
      <div className="weather-widget weather-widget--error" ref={widgetRef}>
        <button
          className="weather-widget-trigger"
          onClick={() => setIsExpanded(!isExpanded)}
          title="Weather unavailable"
        >
          <span className="weather-icon">🌡️</span>
          <span className="weather-error-indicator">!</span>
        </button>
        
        {isExpanded && (
          <div className="weather-widget-dropdown">
            <div className="weather-error">
              <p>{error}</p>
              <button onClick={refreshWeather} className="weather-retry-button">
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="weather-widget" ref={widgetRef}>
      <button
        className="weather-widget-trigger"
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={isLoading && !weather}
        title={weather ? `${weather.location}: ${weather.temperature}°C, ${weather.condition.description}` : 'Loading weather...'}
      >
        {isLoading && !weather ? (
          <span className="weather-loading-indicator">
            <span className="spinner-small" />
          </span>
        ) : weather ? (
          <>
            <span className="weather-icon" aria-hidden="true">
              {getWeatherIcon(weather.condition.main)}
            </span>
            <span className="weather-temp">{weather.temperature}°C</span>
          </>
        ) : null}
      </button>

      {isExpanded && weather && (
        <div className="weather-widget-dropdown">
          <div className="weather-header">
            <h3 className="weather-location">{weather.location}</h3>
            <button
              className="weather-refresh-button"
              onClick={refreshWeather}
              disabled={isLoading}
              title="Refresh weather"
            >
              🔄
            </button>
          </div>

          <div className="weather-main">
            <div className="weather-icon-large">
              {weather.condition.icon && (
                <img
                  src={getWeatherIconUrl(weather.condition.icon)}
                  alt={weather.condition.description}
                />
              )}
            </div>
            <div className="weather-details">
              <div className="weather-temperature">{weather.temperature}°C</div>
              <div className="weather-condition">{weather.condition.description}</div>
            </div>
          </div>

          <div className="weather-extra">
            <div className="weather-extra-item">
              <span className="weather-extra-label">Feels like</span>
              <span className="weather-extra-value">{weather.feelsLike}°C</span>
            </div>
            <div className="weather-extra-item">
              <span className="weather-extra-label">Humidity</span>
              <span className="weather-extra-value">{weather.humidity}%</span>
            </div>
          </div>

          <form className="weather-search" onSubmit={handleLocationSearch}>
            <input
              type="text"
              className="weather-search-input"
              placeholder="Enter city name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              disabled={isSearching}
            />
            <button
              type="submit"
              className="weather-search-button"
              disabled={isSearching || !searchInput.trim()}
            >
              {isSearching ? '...' : 'Go'}
            </button>
          </form>

          <div className="weather-update-time">
            Updated: {weather.lastUpdated.toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
}
