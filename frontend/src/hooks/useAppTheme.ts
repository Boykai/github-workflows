/**
 * Custom hook for managing application theme preferences.
 *
 * When authenticated: reads theme from user settings API, writes changes to
 * both API and localStorage. When unauthenticated: falls back to
 * localStorage only (FR-038).
 */

import { useState, useEffect, useCallback } from 'react';
import { useUserSettings } from '@/hooks/useSettings';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';

export function useAppTheme() {
  const { settings, updateSettings } = useUserSettings();

  const [isDarkMode, setIsDarkMode] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'dark';
  });

  // Sync from API settings when they load (takes precedence over localStorage)
  useEffect(() => {
    if (settings?.display?.theme) {
      const apiDark = settings.display.theme === 'dark';
      setIsDarkMode(apiDark);
      localStorage.setItem(STORAGE_KEY, apiDark ? 'dark' : 'light');
    }
  }, [settings?.display?.theme]);

  // Apply class to document element
  useEffect(() => {
    const rootElement = document.documentElement;
    if (isDarkMode) {
      rootElement.classList.add(DARK_MODE_CLASS);
    } else {
      rootElement.classList.remove(DARK_MODE_CLASS);
    }
  }, [isDarkMode]);

  const toggleTheme = useCallback(() => {
    setIsDarkMode((current) => {
      const newMode = !current;
      const themeValue = newMode ? 'dark' : 'light';
      localStorage.setItem(STORAGE_KEY, themeValue);

      // Save to API if settings are loaded (user is authenticated)
      if (settings) {
        updateSettings({ display: { theme: themeValue as 'dark' | 'light' } }).catch(() => {
          // Silently fail — localStorage is the fallback
        });
      }

      return newMode;
    });
  }, [settings, updateSettings]);

  return {
    isDarkMode,
    toggleTheme,
  };
}
