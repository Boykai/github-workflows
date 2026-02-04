/**
 * Tests for WeatherWidget component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { WeatherWidget } from './WeatherWidget';
import { weatherApi } from '@/services/api';

// Mock the weather API
vi.mock('@/services/api', () => ({
  weatherApi: {
    getCurrent: vi.fn(),
  },
}));

describe('WeatherWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.mocked(weatherApi.getCurrent).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<WeatherWidget />);
    const loadingText = screen.getByText('Loading weather...');
    expect(loadingText).toBeTruthy();
  });

  it('displays weather data when loaded', async () => {
    const mockWeather = {
      temperature: 22.5,
      condition: 'Sunny',
      description: 'clear sky',
      icon: '01d',
      location: 'San Francisco, US',
      humidity: 60,
      wind_speed: 3.2,
      timestamp: Date.now(),
      mock: false,
    };

    vi.mocked(weatherApi.getCurrent).mockResolvedValue(mockWeather);

    render(<WeatherWidget />);

    await waitFor(() => {
      expect(screen.getByText('23')).toBeTruthy(); // Rounded temperature
    });

    expect(screen.getByText('clear sky')).toBeTruthy();
    expect(screen.getByText('San Francisco, US')).toBeTruthy();
  });

  it('displays error state when API fails', async () => {
    vi.mocked(weatherApi.getCurrent).mockRejectedValue(new Error('API Error'));

    render(<WeatherWidget />);

    await waitFor(() => {
      expect(screen.getByText('Unable to fetch weather data')).toBeTruthy();
    });

    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('displays mock data notice when mock flag is true', async () => {
    const mockWeather = {
      temperature: 18.5,
      condition: 'Clouds',
      description: 'partly cloudy',
      icon: '02d',
      location: 'San Francisco, US',
      humidity: 65,
      wind_speed: 3.5,
      timestamp: null,
      mock: true,
    };

    vi.mocked(weatherApi.getCurrent).mockResolvedValue(mockWeather);

    render(<WeatherWidget />);

    await waitFor(() => {
      expect(screen.getByText(/Demo data/)).toBeTruthy();
    });
  });

  it('has proper accessibility attributes', async () => {
    const mockWeather = {
      temperature: 20,
      condition: 'Clear',
      description: 'clear sky',
      icon: '01d',
      location: 'San Francisco, US',
      humidity: 50,
      wind_speed: 2.5,
      timestamp: Date.now(),
      mock: false,
    };

    vi.mocked(weatherApi.getCurrent).mockResolvedValue(mockWeather);

    render(<WeatherWidget />);

    await waitFor(() => {
      expect(screen.getByRole('region', { name: 'Current weather information' })).toBeTruthy();
    });

    // Check for refresh button with aria-label
    const refreshButton = screen.getByRole('button', { name: /Refresh weather/i });
    expect(refreshButton).toBeTruthy();
  });
});
