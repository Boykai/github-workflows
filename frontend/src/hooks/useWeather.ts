/**
 * Custom hook for fetching and managing weather data with caching and auto-refresh.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  fetchWeatherByCoords,
  fetchWeatherByCity,
  getCurrentPosition,
  type WeatherData,
  type WeatherError,
} from '@/services/weather';

const CACHE_KEY = 'tech-connect-weather-cache';
const CITY_KEY = 'tech-connect-weather-city';
const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes in milliseconds

interface CachedWeather {
  data: WeatherData;
  timestamp: number;
}

interface UseWeatherReturn {
  weather: WeatherData | null;
  isLoading: boolean;
  error: Error | null;
  manualCity: string;
  setManualCity: (city: string) => void;
  fetchWeather: () => Promise<void>;
  clearError: () => void;
}

/**
 * Load cached weather data from localStorage
 */
function loadCachedWeather(): WeatherData | null {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const { data, timestamp }: CachedWeather = JSON.parse(cached);
    const age = Date.now() - timestamp;

    // Return cached data if it's less than 30 minutes old
    if (age < CACHE_DURATION) {
      return data;
    }

    // Clear expired cache
    localStorage.removeItem(CACHE_KEY);
    return null;
  } catch (error) {
    console.error('Failed to load cached weather:', error);
    return null;
  }
}

/**
 * Save weather data to localStorage cache
 */
function saveCachedWeather(data: WeatherData): void {
  try {
    const cached: CachedWeather = {
      data,
      timestamp: Date.now(),
    };
    localStorage.setItem(CACHE_KEY, JSON.stringify(cached));
  } catch (error) {
    console.error('Failed to save weather cache:', error);
  }
}

/**
 * Load manual city preference from localStorage
 */
function loadManualCity(): string {
  try {
    return localStorage.getItem(CITY_KEY) || '';
  } catch (error) {
    console.error('Failed to load manual city:', error);
    return '';
  }
}

/**
 * Save manual city preference to localStorage
 */
function saveManualCity(city: string): void {
  try {
    if (city) {
      localStorage.setItem(CITY_KEY, city);
    } else {
      localStorage.removeItem(CITY_KEY);
    }
  } catch (error) {
    console.error('Failed to save manual city:', error);
  }
}

export function useWeather(): UseWeatherReturn {
  const [weather, setWeather] = useState<WeatherData | null>(() => loadCachedWeather());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [manualCity, setManualCityState] = useState<string>(() => loadManualCity());

  const setManualCity = useCallback((city: string) => {
    setManualCityState(city);
    saveManualCity(city);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const fetchWeather = useCallback(async (skipCache = false) => {
    // Check cache first unless explicitly skipped
    if (!skipCache) {
      const cached = loadCachedWeather();
      if (cached) {
        setWeather(cached);
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      let weatherData: WeatherData;

      // Try manual city first if set
      const savedCity = loadManualCity();
      if (savedCity) {
        weatherData = await fetchWeatherByCity(savedCity);
      } else {
        // Try geolocation
        try {
          const position = await getCurrentPosition();
          weatherData = await fetchWeatherByCoords(
            position.coords.latitude,
            position.coords.longitude
          );
        } catch (geoError) {
          // Geolocation failed, set error to prompt for manual city
          const error = geoError as WeatherError;
          if (error.code === 'LOCATION_DENIED') {
            setError(error);
            setIsLoading(false);
            return;
          }
          throw geoError;
        }
      }

      setWeather(weatherData);
      saveCachedWeather(weatherData);
    } catch (err) {
      console.error('Failed to fetch weather:', err);
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []); // No dependencies - function is stable

  // Initial fetch on mount
  useEffect(() => {
    fetchWeather();
  }, [fetchWeather]);

  // Auto-refresh every 30 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchWeather(true); // Skip cache on auto-refresh
    }, CACHE_DURATION);

    return () => clearInterval(interval);
  }, [fetchWeather]);

  // Fetch weather when manual city changes
  useEffect(() => {
    if (manualCity) {
      const fetchByCity = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const weatherData = await fetchWeatherByCity(manualCity);
          setWeather(weatherData);
          saveCachedWeather(weatherData);
        } catch (err) {
          console.error('Failed to fetch weather by city:', err);
          setError(err as Error);
        } finally {
          setIsLoading(false);
        }
      };
      fetchByCity();
    }
  }, [manualCity]);

  return {
    weather,
    isLoading,
    error,
    manualCity,
    setManualCity,
    fetchWeather: () => fetchWeather(true), // Public API always skips cache
    clearError,
  };
}
