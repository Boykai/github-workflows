/**
 * Unit tests for WeatherWidget component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WeatherWidget } from './WeatherWidget';
import * as useWeatherHook from '@/hooks/useWeather';
import type { ReactNode } from 'react';

// Mock the useWeather hook
vi.mock('@/hooks/useWeather');

const mockUseWeather = useWeatherHook.useWeather as unknown as ReturnType<typeof vi.fn>;

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

describe('WeatherWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show loading state while fetching weather', () => {
    vi.mocked(mockUseWeather).mockReturnValue({
      weather: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<WeatherWidget />, { wrapper: createWrapper() });

    expect(screen.getByText('Loading weather...')).toBeTruthy();
  });

  it('should show error state when weather fetch fails', () => {
    vi.mocked(mockUseWeather).mockReturnValue({
      weather: null,
      isLoading: false,
      error: new Error('Failed to fetch'),
      refetch: vi.fn(),
    });

    render(<WeatherWidget />, { wrapper: createWrapper() });

    expect(screen.getByText('Weather unavailable')).toBeTruthy();
  });

  it('should display weather data when loaded', () => {
    const mockWeather = {
      location: 'San Francisco',
      temperature: 18,
      condition: 'Clear',
      description: 'Clear sky',
      icon: '01d',
    };

    vi.mocked(mockUseWeather).mockReturnValue({
      weather: mockWeather,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<WeatherWidget />, { wrapper: createWrapper() });

    expect(screen.getByText('18°C')).toBeTruthy();
    expect(screen.getByText('San Francisco')).toBeTruthy();
    expect(screen.getByText('Clear sky')).toBeTruthy();
  });

  it('should display correct weather icon emoji for clear sky', () => {
    const mockWeather = {
      location: 'San Francisco',
      temperature: 18,
      condition: 'Clear',
      description: 'Clear sky',
      icon: '01d',
    };

    vi.mocked(mockUseWeather).mockReturnValue({
      weather: mockWeather,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<WeatherWidget />, { wrapper: createWrapper() });

    const weatherIcon = container.querySelector('.weather-icon');
    expect(weatherIcon?.textContent).toBe('☀️');
  });

  it('should display correct weather icon emoji for rain', () => {
    const mockWeather = {
      location: 'Seattle',
      temperature: 12,
      condition: 'Rain',
      description: 'Light rain',
      icon: '10d',
    };

    vi.mocked(mockUseWeather).mockReturnValue({
      weather: mockWeather,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<WeatherWidget />, { wrapper: createWrapper() });

    const weatherIcon = container.querySelector('.weather-icon');
    expect(weatherIcon?.textContent).toBe('🌦️');
  });

  it('should return null when weather is null and not loading', () => {
    vi.mocked(mockUseWeather).mockReturnValue({
      weather: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<WeatherWidget />, { wrapper: createWrapper() });

    expect(container.firstChild).toBeNull();
  });

  it('should round temperature to nearest integer', () => {
    const mockWeather = {
      location: 'San Francisco',
      temperature: 18.7,
      condition: 'Clear',
      description: 'Clear sky',
      icon: '01d',
    };

    vi.mocked(mockUseWeather).mockReturnValue({
      weather: mockWeather,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<WeatherWidget />, { wrapper: createWrapper() });

    expect(screen.getByText('19°C')).toBeTruthy();
  });
});
