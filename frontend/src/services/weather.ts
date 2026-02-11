/**
 * Weather service for fetching current weather data.
 * Uses OpenWeatherMap API for weather information.
 */

export interface WeatherData {
  temperature: number; // in Celsius
  condition: string; // e.g., 'Clear', 'Clouds', 'Rain'
  description: string; // e.g., 'clear sky', 'few clouds'
  icon: string; // weather icon code
  city: string;
  country: string;
}

export interface GeolocationCoords {
  latitude: number;
  longitude: number;
}

const WEATHER_API_KEY = import.meta.env.VITE_WEATHER_API_KEY || 'demo'; // Demo key for development
const WEATHER_API_BASE = 'https://api.openweathermap.org/data/2.5';

/**
 * Get current weather by coordinates.
 */
export async function getWeatherByCoords(
  coords: GeolocationCoords
): Promise<WeatherData> {
  const { latitude, longitude } = coords;
  const url = `${WEATHER_API_BASE}/weather?lat=${latitude}&lon=${longitude}&units=metric&appid=${WEATHER_API_KEY}`;

  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Weather API error: ${response.statusText}`);
  }

  const data = await response.json();

  return {
    temperature: Math.round(data.main.temp),
    condition: data.weather[0].main,
    description: data.weather[0].description,
    icon: data.weather[0].icon,
    city: data.name,
    country: data.sys.country,
  };
}

/**
 * Get current weather by city name.
 */
export async function getWeatherByCity(city: string): Promise<WeatherData> {
  const url = `${WEATHER_API_BASE}/weather?q=${encodeURIComponent(city)}&units=metric&appid=${WEATHER_API_KEY}`;

  const response = await fetch(url);
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('City not found');
    }
    throw new Error(`Weather API error: ${response.statusText}`);
  }

  const data = await response.json();

  return {
    temperature: Math.round(data.main.temp),
    condition: data.weather[0].main,
    description: data.weather[0].description,
    icon: data.weather[0].icon,
    city: data.name,
    country: data.sys.country,
  };
}

/**
 * Request user's geolocation.
 */
export function requestGeolocation(): Promise<GeolocationCoords> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by your browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      (error) => {
        reject(new Error(error.message));
      },
      {
        timeout: 10000,
        enableHighAccuracy: false,
      }
    );
  });
}

/**
 * Get weather icon URL from OpenWeatherMap.
 */
export function getWeatherIconUrl(iconCode: string): string {
  return `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
}
