/**
 * Unit tests for useWeather hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useWeather } from './useWeather';
import * as weatherService from '@/services/weather';

// Mock the weather service
vi.mock('@/services/weather', () => ({
  fetchWeatherByCoords: vi.fn(),
  fetchWeatherByCity: vi.fn(),
  getCurrentPosition: vi.fn(),
  getWeatherIconUrl: vi.fn((icon) => `https://openweathermap.org/img/wn/${icon}@2x.png`),
}));

const mockWeatherService = weatherService as {
  fetchWeatherByCoords: ReturnType<typeof vi.fn>;
  fetchWeatherByCity: ReturnType<typeof vi.fn>;
  getCurrentPosition: ReturnType<typeof vi.fn>;
  getWeatherIconUrl: (icon: string) => string;
};

describe('useWeather', () => {
  const mockWeatherData = {
    location: 'San Francisco',
    temperature: 18,
    condition: 'Clear',
    description: 'clear sky',
    icon: '01d',
    timestamp: Date.now(),
  };

  const mockPosition = {
    coords: {
      latitude: 37.7749,
      longitude: -122.4194,
    },
  } as GeolocationPosition;

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    
    // Reset all mocks
    vi.clearAllMocks();

    // Mock successful geolocation by default
    mockWeatherService.getCurrentPosition.mockResolvedValue(mockPosition);
    mockWeatherService.fetchWeatherByCoords.mockResolvedValue(mockWeatherData);
    mockWeatherService.fetchWeatherByCity.mockResolvedValue(mockWeatherData);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('should fetch weather using geolocation on mount', async () => {
    const { result } = renderHook(() => useWeather());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockWeatherService.getCurrentPosition).toHaveBeenCalledTimes(1);
    expect(mockWeatherService.fetchWeatherByCoords).toHaveBeenCalledWith(
      mockPosition.coords.latitude,
      mockPosition.coords.longitude
    );
    expect(result.current.weather).toEqual(mockWeatherData);
    expect(result.current.error).toBeNull();
  });

  it('should use cached weather data if available and fresh', async () => {
    // Set up fresh cache
    const cachedData = {
      data: mockWeatherData,
      timestamp: Date.now() - 5 * 60 * 1000, // 5 minutes ago
    };
    localStorage.setItem('tech-connect-weather-cache', JSON.stringify(cachedData));

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.weather).toEqual(mockWeatherData);
    });

    // Should not fetch if cache is fresh
    expect(mockWeatherService.getCurrentPosition).not.toHaveBeenCalled();
    expect(mockWeatherService.fetchWeatherByCoords).not.toHaveBeenCalled();
  });

  it('should fetch new data if cache is expired', async () => {
    // Set up expired cache (older than 30 minutes)
    const cachedData = {
      data: mockWeatherData,
      timestamp: Date.now() - 35 * 60 * 1000, // 35 minutes ago
    };
    localStorage.setItem('tech-connect-weather-cache', JSON.stringify(cachedData));

    const { result } = renderHook(() => useWeather());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should fetch new data since cache expired
    expect(mockWeatherService.getCurrentPosition).toHaveBeenCalledTimes(1);
    expect(mockWeatherService.fetchWeatherByCoords).toHaveBeenCalledTimes(1);
  });

  it('should handle geolocation denial and show error', async () => {
    const locationError = new Error('Location access denied. Please enter your city manually.');
    (locationError as any).code = 'LOCATION_DENIED';
    mockWeatherService.getCurrentPosition.mockRejectedValue(locationError);

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toEqual(locationError);
    expect(result.current.weather).toBeNull();
  });

  it('should fetch weather by manual city when set', async () => {
    const cityWeather = { ...mockWeatherData, location: 'New York' };
    mockWeatherService.fetchWeatherByCity.mockResolvedValue(cityWeather);

    const { result } = renderHook(() => useWeather());

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Set manual city
    act(() => {
      result.current.setManualCity('New York');
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockWeatherService.fetchWeatherByCity).toHaveBeenCalledWith('New York');
    expect(result.current.weather).toEqual(cityWeather);
    expect(result.current.manualCity).toBe('New York');
  });

  it('should save manual city to localStorage', async () => {
    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setManualCity('London');
    });

    await waitFor(() => {
      expect(localStorage.getItem('tech-connect-weather-city')).toBe('London');
    });
  });

  it('should use manual city preference on mount if available', async () => {
    localStorage.setItem('tech-connect-weather-city', 'Tokyo');
    const tokyoWeather = { ...mockWeatherData, location: 'Tokyo' };
    mockWeatherService.fetchWeatherByCity.mockResolvedValue(tokyoWeather);

    const { result } = renderHook(() => useWeather());

    expect(result.current.manualCity).toBe('Tokyo');

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockWeatherService.fetchWeatherByCity).toHaveBeenCalledWith('Tokyo');
    expect(result.current.weather).toEqual(tokyoWeather);
    // Should not use geolocation if manual city is set
    expect(mockWeatherService.getCurrentPosition).not.toHaveBeenCalled();
  });

  it('should handle API errors gracefully', async () => {
    const apiError = new Error('Weather API request failed: 500 Internal Server Error');
    (apiError as any).code = 'API_ERROR';
    mockWeatherService.fetchWeatherByCoords.mockRejectedValue(apiError);

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toEqual(apiError);
    expect(result.current.weather).toBeNull();
  });

  it('should clear error when clearError is called', async () => {
    const error = new Error('Test error');
    mockWeatherService.fetchWeatherByCoords.mockRejectedValue(error);

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.error).toEqual(error);
    });

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('should cache weather data to localStorage', async () => {
    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.weather).toEqual(mockWeatherData);
    });

    const cached = JSON.parse(localStorage.getItem('tech-connect-weather-cache') || '{}');
    expect(cached.data).toEqual(mockWeatherData);
    expect(cached.timestamp).toBeGreaterThan(Date.now() - 1000);
  });

  it('should auto-refresh weather after 30 minutes', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useWeather());

    await waitFor(() => {
      expect(result.current.weather).toEqual(mockWeatherData);
    });

    // Clear the initial fetch call
    vi.clearAllMocks();

    // Fast-forward 30 minutes
    act(() => {
      vi.advanceTimersByTime(30 * 60 * 1000);
    });

    await waitFor(() => {
      expect(mockWeatherService.fetchWeatherByCoords).toHaveBeenCalled();
    });

    vi.useRealTimers();
  });
});
