/**
 * Custom hook for managing weather data
 */

import { useState, useEffect, useCallback } from 'react';
import type { WeatherData } from '@/types/weather';
import {
  fetchWeatherByCoords,
  fetchWeatherByCity,
  getUserLocation,
  WeatherServiceError,
} from '@/services/weather';

const REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutes in milliseconds
const STORAGE_KEY = 'weather_location';

interface UseWeatherReturn {
  weather: WeatherData | null;
  isLoading: boolean;
  error: string | null;
  refreshWeather: () => Promise<void>;
  setLocation: (city: string) => Promise<void>;
}

export function useWeather(): UseWeatherReturn {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch weather for user's current location
   */
  const fetchWeatherForCurrentLocation = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const location = await getUserLocation();
      const data = await fetchWeatherByCoords(location.lat, location.lon);
      
      setWeather(data);
      // Clear saved location when using current location
      localStorage.removeItem(STORAGE_KEY);
    } catch (err) {
      if (err instanceof WeatherServiceError) {
        setError(err.message);
      } else {
        setError('Failed to fetch weather data');
      }
      console.error('Weather fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch weather for a specific city
   */
  const fetchWeatherForCity = useCallback(async (city: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const data = await fetchWeatherByCity(city);
      
      setWeather(data);
      // Save the city name for future loads
      localStorage.setItem(STORAGE_KEY, city);
    } catch (err) {
      if (err instanceof WeatherServiceError) {
        setError(err.message);
      } else {
        setError('Failed to fetch weather data');
      }
      console.error('Weather fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh weather data based on current state
   */
  const refreshWeather = useCallback(async () => {
    const savedLocation = localStorage.getItem(STORAGE_KEY);
    
    if (savedLocation) {
      await fetchWeatherForCity(savedLocation);
    } else {
      await fetchWeatherForCurrentLocation();
    }
  }, [fetchWeatherForCity, fetchWeatherForCurrentLocation]);

  /**
   * Set a specific location
   */
  const setLocation = useCallback(
    async (city: string) => {
      await fetchWeatherForCity(city);
    },
    [fetchWeatherForCity]
  );

  // Initial load
  useEffect(() => {
    refreshWeather();
  }, [refreshWeather]);

  // Set up auto-refresh interval
  useEffect(() => {
    const intervalId = setInterval(() => {
      refreshWeather();
    }, REFRESH_INTERVAL);

    return () => clearInterval(intervalId);
  }, [refreshWeather]);

  return {
    weather,
    isLoading,
    error,
    refreshWeather,
    setLocation,
  };
}
