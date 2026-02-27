/**
 * Custom hook for managing application theme preferences.
 *
 * Delegates to the ThemeProvider context so the `dark` / `light` class on
 * <html> stays in sync with the Tailwind CSS variable layer in index.css.
 *
 * When authenticated: syncs theme from user settings API on load, and
 * persists toggles back to API + localStorage. When unauthenticated: falls
 * back to localStorage only (FR-038).
 */

import { useEffect, useCallback } from 'react';
import { useTheme } from '@/components/ThemeProvider';
import { useUserSettings } from '@/hooks/useSettings';

export function useAppTheme() {
  const { theme, setTheme } = useTheme();
  const { settings, updateSettings } = useUserSettings();

  // Resolve the effective boolean — "system" defers to the OS preference.
  const isDarkMode =
    theme === 'dark' ||
    (theme === 'system' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);

  // Sync from API settings when they load (takes precedence over localStorage)
  useEffect(() => {
    if (settings?.display?.theme) {
      setTheme(settings.display.theme);
    }
  }, [settings?.display?.theme, setTheme]);

  const toggleTheme = useCallback(() => {
    const newTheme = isDarkMode ? 'light' : 'dark';
    setTheme(newTheme);

    // Save to API if settings are loaded (user is authenticated)
    if (settings) {
      updateSettings({ display: { theme: newTheme } }).catch(() => {
        // Silently fail — localStorage is the fallback
      });
    }
  }, [isDarkMode, setTheme, settings, updateSettings]);

  return {
    isDarkMode,
    toggleTheme,
  };
}
