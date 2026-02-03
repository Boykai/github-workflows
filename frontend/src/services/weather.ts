/**
 * Weather service for fetching weather data
 * Uses OpenWeatherMap API
 */

import type { WeatherData, WeatherError } from '@/types/weather';

// Using OpenWeatherMap API - free tier available
const WEATHER_API_KEY = import.meta.env.VITE_WEATHER_API_KEY || 'demo';
const WEATHER_API_BASE = 'https://api.openweathermap.org/data/2.5';

export class WeatherServiceError extends Error {
  constructor(
    public code: string,
    message: string
  ) {
    super(message);
    this.name = 'WeatherServiceError';
  }
}

/**
 * Get current user's location using browser Geolocation API
 */
export async function getUserLocation(): Promise<{ lat: number; lon: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new WeatherServiceError('GEOLOCATION_NOT_SUPPORTED', 'Geolocation is not supported by your browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
      },
      (error) => {
        reject(new WeatherServiceError('GEOLOCATION_ERROR', error.message));
      },
      { timeout: 10000 }
    );
  });
}

/**
 * Fetch weather data by coordinates
 */
export async function fetchWeatherByCoords(lat: number, lon: number): Promise<WeatherData> {
  try {
    const url = `${WEATHER_API_BASE}/weather?lat=${lat}&lon=${lon}&units=metric&appid=${WEATHER_API_KEY}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new WeatherServiceError('API_ERROR', `Weather API returned ${response.status}`);
    }

    const data = await response.json();
    
    return {
      location: data.name,
      temperature: Math.round(data.main.temp),
      condition: {
        main: data.weather[0].main,
        description: data.weather[0].description,
        icon: data.weather[0].icon,
      },
      feelsLike: Math.round(data.main.feels_like),
      humidity: data.main.humidity,
      lastUpdated: new Date(),
    };
  } catch (error) {
    if (error instanceof WeatherServiceError) {
      throw error;
    }
    throw new WeatherServiceError('FETCH_ERROR', 'Failed to fetch weather data');
  }
}

/**
 * Fetch weather data by city name
 */
export async function fetchWeatherByCity(city: string): Promise<WeatherData> {
  try {
    const url = `${WEATHER_API_BASE}/weather?q=${encodeURIComponent(city)}&units=metric&appid=${WEATHER_API_KEY}`;
    const response = await fetch(url);

    if (!response.ok) {
      if (response.status === 404) {
        throw new WeatherServiceError('CITY_NOT_FOUND', 'City not found');
      }
      throw new WeatherServiceError('API_ERROR', `Weather API returned ${response.status}`);
    }

    const data = await response.json();
    
    return {
      location: data.name,
      temperature: Math.round(data.main.temp),
      condition: {
        main: data.weather[0].main,
        description: data.weather[0].description,
        icon: data.weather[0].icon,
      },
      feelsLike: Math.round(data.main.feels_like),
      humidity: data.main.humidity,
      lastUpdated: new Date(),
    };
  } catch (error) {
    if (error instanceof WeatherServiceError) {
      throw error;
    }
    throw new WeatherServiceError('FETCH_ERROR', 'Failed to fetch weather data');
  }
}

/**
 * Get weather icon URL from OpenWeatherMap
 */
export function getWeatherIconUrl(iconCode: string): string {
  return `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
}
