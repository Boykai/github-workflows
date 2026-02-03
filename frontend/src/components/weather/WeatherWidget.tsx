/**
 * Weather widget component.
 * Displays current weather information with loading and error states.
 */

import { useWeather } from '@/hooks/useWeather';
import './WeatherWidget.css';

export function WeatherWidget() {
  const { weather, isLoading, error } = useWeather();

  if (isLoading) {
    return (
      <div className="weather-widget weather-widget--loading">
        <div className="weather-spinner" />
        <span className="weather-loading-text">Loading weather...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weather-widget weather-widget--error">
        <span className="weather-error-icon">⚠️</span>
        <span className="weather-error-text">Weather unavailable</span>
      </div>
    );
  }

  if (!weather) {
    return null;
  }

  // Map OpenWeatherMap icon codes to emoji (simplified)
  const getWeatherEmoji = (icon: string): string => {
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
    return iconMap[icon] || '🌤️';
  };

  return (
    <div className="weather-widget">
      <div className="weather-icon">{getWeatherEmoji(weather.icon)}</div>
      <div className="weather-info">
        <div className="weather-temperature">{Math.round(weather.temperature)}°C</div>
        <div className="weather-location">{weather.location}</div>
      </div>
      <div className="weather-description">{weather.description}</div>
    </div>
  );
}
