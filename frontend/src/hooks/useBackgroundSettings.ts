/**
 * Hook to manage chat background settings with localStorage persistence.
 */

import { useState, useEffect } from 'react';

export type BackgroundType = 'preset' | 'custom' | 'default';

export interface BackgroundSettings {
  type: BackgroundType;
  value: string; // CSS value for preset/default, data URL for custom
}

const DEFAULT_BACKGROUND: BackgroundSettings = {
  type: 'default',
  value: 'var(--color-bg)',
};

export const PRESET_BACKGROUNDS = [
  { id: 'gradient-blue', name: 'Ocean Blue', value: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { id: 'gradient-sunset', name: 'Sunset', value: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { id: 'gradient-forest', name: 'Forest', value: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { id: 'gradient-purple', name: 'Purple Dream', value: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' },
  { id: 'gradient-dark', name: 'Dark Mode', value: 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)' },
];

const STORAGE_KEY = 'chat_background_settings';

export function useBackgroundSettings() {
  const [background, setBackground] = useState<BackgroundSettings>(DEFAULT_BACKGROUND);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as BackgroundSettings;
        setBackground(parsed);
      } catch (error) {
        console.error('Failed to parse background settings:', error);
      }
    }
  }, []);

  // Save to localStorage when background changes
  const updateBackground = (newBackground: BackgroundSettings) => {
    setBackground(newBackground);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newBackground));
  };

  const setPresetBackground = (presetValue: string) => {
    updateBackground({
      type: 'preset',
      value: presetValue,
    });
  };

  const setCustomBackground = (imageDataUrl: string) => {
    updateBackground({
      type: 'custom',
      value: imageDataUrl,
    });
  };

  const resetToDefault = () => {
    updateBackground(DEFAULT_BACKGROUND);
  };

  return {
    background,
    setPresetBackground,
    setCustomBackground,
    resetToDefault,
  };
}
