/**
 * Tests for useWeather hook.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWeather } from './useWeather';
import * as weatherService from '@/services/weather';

// Mock the weather service
vi.mock('@/services/weather', () => ({
  getWeatherByCoords: vi.fn(),
  getWeatherByCity: vi.fn(),
  requestGeolocation: vi.fn(),
  getWeatherIconUrl: vi.fn((code) => `https://openweathermap.org/img/wn/${code}@2x.png`),
}));

const mockWeatherData = {
  temperature: 20,
  condition: 'Clear',
  description: 'clear sky',
  icon: '01d',
  city: 'San Francisco',
  country: 'US',
};

describe('useWeather', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('should fetch weather by location on mount', async () => {
    const mockCoords = { latitude: 37.7749, longitude: -122.4194 };
    vi.mocked(weatherService.requestGeolocation).mockResolvedValue(mockCoords);
    vi.mocked(weatherService.getWeatherByCoords).mockResolvedValue(mockWeatherData);

    const { result } = renderHook(() => useWeather());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.weather).toEqual(mockWeatherData);
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(weatherService.requestGeolocation).toHaveBeenCalled();
    expect(weatherService.getWeatherByCoords).toHaveBeenCalledWith(mockCoords);
  });

  it('should handle location denied error', async () => {
    vi.mocked(weatherService.requestGeolocation).mockRejectedValue(
      new Error('User denied geolocation')
    );

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.locationDenied).toBe(true);
    });

    expect(result.current.error).toContain('Location access denied');
    expect(result.current.weather).toBe(null);
  });

  it('should fetch weather by city name', async () => {
    vi.mocked(weatherService.requestGeolocation).mockRejectedValue(
      new Error('User denied geolocation')
    );
    vi.mocked(weatherService.getWeatherByCity).mockResolvedValue(mockWeatherData);

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.locationDenied).toBe(true);
    });

    // Fetch weather by city
    await result.current.fetchWeatherByCity('San Francisco');

    await waitFor(() => {
      expect(result.current.weather).toEqual(mockWeatherData);
    });

    expect(weatherService.getWeatherByCity).toHaveBeenCalledWith('San Francisco');
  });

  it('should cache weather data in localStorage', async () => {
    const mockCoords = { latitude: 37.7749, longitude: -122.4194 };
    vi.mocked(weatherService.requestGeolocation).mockResolvedValue(mockCoords);
    vi.mocked(weatherService.getWeatherByCoords).mockResolvedValue(mockWeatherData);

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.weather).toEqual(mockWeatherData);
    });

    const cached = localStorage.getItem('tech-connect-weather-cache');
    expect(cached).toBeTruthy();
    const parsedCache = JSON.parse(cached!);
    expect(parsedCache.data).toEqual(mockWeatherData);
  });

  it('should load cached weather data on mount', async () => {
    // Set up cached data
    const cacheData = {
      data: mockWeatherData,
      timestamp: Date.now(),
    };
    localStorage.setItem('tech-connect-weather-cache', JSON.stringify(cacheData));

    vi.mocked(weatherService.requestGeolocation).mockResolvedValue({
      latitude: 37.7749,
      longitude: -122.4194,
    });

    const { result } = renderHook(() => useWeather());

    // Should load from cache immediately
    await waitFor(() => {
      expect(result.current.weather).toEqual(mockWeatherData);
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('should handle city not found error', async () => {
    vi.mocked(weatherService.requestGeolocation).mockRejectedValue(
      new Error('User denied geolocation')
    );
    vi.mocked(weatherService.getWeatherByCity).mockRejectedValue(
      new Error('City not found')
    );

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.locationDenied).toBe(true);
    });

    await result.current.fetchWeatherByCity('InvalidCity123');

    await waitFor(() => {
      expect(result.current.error).toContain('City not found');
    });
  });
});
