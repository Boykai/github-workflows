/**
 * Weather data types for the weather widget
 */

export interface WeatherCondition {
  main: string;
  description: string;
  icon: string;
}

export interface WeatherData {
  location: string;
  temperature: number;
  condition: WeatherCondition;
  feelsLike: number;
  humidity: number;
  lastUpdated: Date;
}

export interface WeatherError {
  message: string;
  code?: string;
}
