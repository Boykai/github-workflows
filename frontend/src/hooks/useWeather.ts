/**
 * Custom hook for managing weather data and location permissions.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getWeatherByCoords,
  getWeatherByCity,
  requestGeolocation,
  type WeatherData,
} from '@/services/weather';

const WEATHER_CACHE_KEY = 'tech-connect-weather-cache';
const WEATHER_CITY_KEY = 'tech-connect-weather-city';
const WEATHER_REFRESH_INTERVAL = 30 * 60 * 1000; // 30 minutes

interface WeatherCache {
  data: WeatherData;
  timestamp: number;
}

interface UseWeatherReturn {
  weather: WeatherData | null;
  isLoading: boolean;
  error: string | null;
  locationDenied: boolean;
  manualCity: string;
  setManualCity: (city: string) => void;
  fetchWeatherByCity: (city: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useWeather(): UseWeatherReturn {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [locationDenied, setLocationDenied] = useState(false);
  const [manualCity, setManualCity] = useState('');

  // Load cached weather data
  const loadCache = useCallback((): WeatherData | null => {
    try {
      const cached = localStorage.getItem(WEATHER_CACHE_KEY);
      if (cached) {
        const { data, timestamp }: WeatherCache = JSON.parse(cached);
        // Check if cache is still fresh (less than 30 minutes old)
        if (Date.now() - timestamp < WEATHER_REFRESH_INTERVAL) {
          return data;
        }
      }
    } catch (err) {
      console.error('Failed to load weather cache:', err);
    }
    return null;
  }, []);

  // Save weather data to cache
  const saveCache = useCallback((data: WeatherData) => {
    try {
      const cache: WeatherCache = {
        data,
        timestamp: Date.now(),
      };
      localStorage.setItem(WEATHER_CACHE_KEY, JSON.stringify(cache));
    } catch (err) {
      console.error('Failed to save weather cache:', err);
    }
  }, []);

  // Fetch weather by geolocation
  const fetchWeatherByLocation = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const coords = await requestGeolocation();
      const data = await getWeatherByCoords(coords);
      setWeather(data);
      saveCache(data);
      setLocationDenied(false);
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('denied') || err.message.includes('permission')) {
          setLocationDenied(true);
          setError('Location access denied. Please enter a city manually.');
        } else {
          setError(err.message);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [saveCache]);

  // Fetch weather by city name
  const fetchWeatherByCity = useCallback(
    async (city: string) => {
      if (!city.trim()) {
        setError('Please enter a city name');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data = await getWeatherByCity(city);
        setWeather(data);
        saveCache(data);
        localStorage.setItem(WEATHER_CITY_KEY, city);
        setManualCity(city);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [saveCache]
  );

  // Refresh weather data
  const refresh = useCallback(async () => {
    const savedCity = localStorage.getItem(WEATHER_CITY_KEY);
    if (savedCity) {
      await fetchWeatherByCity(savedCity);
    } else {
      await fetchWeatherByLocation();
    }
  }, [fetchWeatherByCity, fetchWeatherByLocation]);

  // Initial load
  useEffect(() => {
    const cachedWeather = loadCache();
    const savedCity = localStorage.getItem(WEATHER_CITY_KEY);

    if (cachedWeather) {
      setWeather(cachedWeather);
      setIsLoading(false);
      if (savedCity) {
        setManualCity(savedCity);
      }
    } else if (savedCity) {
      setManualCity(savedCity);
      fetchWeatherByCity(savedCity);
    } else {
      fetchWeatherByLocation();
    }

    // Set up auto-refresh interval
    const intervalId = setInterval(() => {
      refresh();
    }, WEATHER_REFRESH_INTERVAL);

    return () => clearInterval(intervalId);
  }, [loadCache, fetchWeatherByCity, fetchWeatherByLocation, refresh]);

  return {
    weather,
    isLoading,
    error,
    locationDenied,
    manualCity,
    setManualCity,
    fetchWeatherByCity,
    refresh,
  };
}
