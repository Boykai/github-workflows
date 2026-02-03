/**
 * Hook for fetching and managing weather data.
 */

import { useQuery } from '@tanstack/react-query';
import { weatherApi } from '@/services/api';
import type { WeatherData } from '@/types';

export interface UseWeatherResult {
  weather: WeatherData | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch current weather data.
 * Data is cached and refetched on mount and when explicitly refetched.
 */
export function useWeather(): UseWeatherResult {
  const {
    data: weather = null,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['weather'],
    queryFn: () => weatherApi.getCurrentWeather(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: 2,
    retryDelay: 1000,
  });

  return {
    weather,
    isLoading,
    error: error as Error | null,
    refetch: () => {
      refetch();
    },
  };
}
