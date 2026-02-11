/**
 * Weather service for fetching weather data from OpenWeatherMap API.
 */

// Weather data interfaces
export interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  description: string;
  icon: string;
  timestamp: number;
}

export interface WeatherError extends Error {
  code: 'API_KEY_MISSING' | 'LOCATION_DENIED' | 'API_ERROR' | 'NETWORK_ERROR';
}

// Get API key from environment
const API_KEY = import.meta.env.VITE_WEATHER_API_KEY;
const API_BASE_URL = 'https://api.openweathermap.org/data/2.5';

/**
 * Validate API key configuration
 */
function validateApiKey(): void {
  if (!API_KEY || API_KEY === 'demo' || API_KEY === 'your_openweathermap_api_key') {
    const error = new Error(
      'Weather API key is not configured. Please set VITE_WEATHER_API_KEY in your .env file.'
    ) as WeatherError;
    error.code = 'API_KEY_MISSING';
    throw error;
  }
}

/**
 * Fetch weather data by coordinates
 */
export async function fetchWeatherByCoords(
  latitude: number,
  longitude: number
): Promise<WeatherData> {
  validateApiKey();

  try {
    const response = await fetch(
      `${API_BASE_URL}/weather?lat=${latitude}&lon=${longitude}&units=metric&appid=${API_KEY}`
    );

    if (!response.ok) {
      const error = new Error(
        `Weather API request failed: ${response.status} ${response.statusText}`
      ) as WeatherError;
      error.code = 'API_ERROR';
      throw error;
    }

    const data = await response.json();
    
    return {
      location: data.name || 'Unknown',
      temperature: Math.round(data.main.temp),
      condition: data.weather[0]?.main || 'Unknown',
      description: data.weather[0]?.description || '',
      icon: data.weather[0]?.icon || '01d',
      timestamp: Date.now(),
    };
  } catch (error) {
    if (error instanceof Error && 'code' in error) {
      throw error;
    }
    const networkError = new Error(
      'Failed to fetch weather data. Please check your internet connection.'
    ) as WeatherError;
    networkError.code = 'NETWORK_ERROR';
    throw networkError;
  }
}

/**
 * Fetch weather data by city name
 */
export async function fetchWeatherByCity(city: string): Promise<WeatherData> {
  validateApiKey();

  if (!city || city.trim() === '') {
    throw new Error('City name is required');
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/weather?q=${encodeURIComponent(city)}&units=metric&appid=${API_KEY}`
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`City "${city}" not found. Please check the spelling and try again.`);
      }
      const error = new Error(
        `Weather API request failed: ${response.status} ${response.statusText}`
      ) as WeatherError;
      error.code = 'API_ERROR';
      throw error;
    }

    const data = await response.json();
    
    return {
      location: data.name || city,
      temperature: Math.round(data.main.temp),
      condition: data.weather[0]?.main || 'Unknown',
      description: data.weather[0]?.description || '',
      icon: data.weather[0]?.icon || '01d',
      timestamp: Date.now(),
    };
  } catch (error) {
    if (error instanceof Error && error.message.includes('not found')) {
      throw error;
    }
    if (error instanceof Error && 'code' in error) {
      throw error;
    }
    const networkError = new Error(
      'Failed to fetch weather data. Please check your internet connection.'
    ) as WeatherError;
    networkError.code = 'NETWORK_ERROR';
    throw networkError;
  }
}

/**
 * Get weather icon URL from OpenWeatherMap
 */
export function getWeatherIconUrl(iconCode: string): string {
  return `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
}

/**
 * Get user's geolocation coordinates
 */
export function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      const error = new Error(
        'Geolocation is not supported by your browser'
      ) as WeatherError;
      error.code = 'LOCATION_DENIED';
      reject(error);
      return;
    }

    navigator.geolocation.getCurrentPosition(resolve, (error) => {
      const locationError = new Error(
        error.code === error.PERMISSION_DENIED
          ? 'Location access denied. Please enter your city manually.'
          : 'Unable to retrieve your location. Please enter your city manually.'
      ) as WeatherError;
      locationError.code = 'LOCATION_DENIED';
      reject(locationError);
    });
  });
}
