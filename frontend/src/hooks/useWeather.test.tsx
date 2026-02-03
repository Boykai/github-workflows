/**
 * Unit tests for useWeather hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWeather } from './useWeather';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

// Mock the API module
vi.mock('@/services/api', () => ({
  weatherApi: {
    getCurrentWeather: vi.fn(),
  },
}));

const mockWeatherApi = api.weatherApi as unknown as {
  getCurrentWeather: ReturnType<typeof vi.fn>;
};

// Create wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('useWeather', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should return null weather initially when loading', () => {
    mockWeatherApi.getCurrentWeather.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(() => useWeather(), {
      wrapper: createWrapper(),
    });

    expect(result.current.weather).toBeNull();
    expect(result.current.isLoading).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should fetch and return weather data', async () => {
    const mockWeather = {
      location: 'San Francisco',
      temperature: 18,
      condition: 'Clear',
      description: 'Clear sky',
      icon: '01d',
      humidity: 65,
      windSpeed: 12,
    };

    mockWeatherApi.getCurrentWeather.mockResolvedValue(mockWeather);

    const { result } = renderHook(() => useWeather(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.weather).toEqual(mockWeather);
    expect(result.current.error).toBeNull();
  });

  it('should handle errors when fetching weather fails', async () => {
    const mockError = new Error('Failed to fetch weather');
    mockWeatherApi.getCurrentWeather.mockRejectedValue(mockError);

    const { result } = renderHook(() => useWeather(), {
      wrapper: createWrapper(),
    });

    await waitFor(
      () => {
        expect(result.current.error).toBeTruthy();
      },
      { timeout: 5000 }
    );

    expect(result.current.weather).toBeNull();
  });

  it('should have a refetch function', async () => {
    const mockWeather = {
      location: 'San Francisco',
      temperature: 18,
      condition: 'Clear',
      description: 'Clear sky',
      icon: '01d',
    };

    mockWeatherApi.getCurrentWeather.mockResolvedValue(mockWeather);

    const { result } = renderHook(() => useWeather(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(typeof result.current.refetch).toBe('function');
  });

  it('should display correct temperature and location', async () => {
    const mockWeather = {
      location: 'New York',
      temperature: 25,
      condition: 'Sunny',
      description: 'Sunny day',
      icon: '01d',
    };

    mockWeatherApi.getCurrentWeather.mockResolvedValue(mockWeather);

    const { result } = renderHook(() => useWeather(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.weather?.location).toBe('New York');
    expect(result.current.weather?.temperature).toBe(25);
  });
});
