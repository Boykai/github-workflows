/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';
const RAINBOW_MODE_CLASS = 'rainbow-mode-active';

export type ThemeMode = 'light' | 'dark' | 'rainbow';

const THEME_CYCLE: ThemeMode[] = ['light', 'dark', 'rainbow'];

export function useAppTheme() {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'rainbow') return stored;
    return 'light';
  });

  useEffect(() => {
    const rootElement = document.documentElement;
    rootElement.classList.remove(DARK_MODE_CLASS, RAINBOW_MODE_CLASS);
    if (theme === 'dark') {
      rootElement.classList.add(DARK_MODE_CLASS);
    } else if (theme === 'rainbow') {
      rootElement.classList.add(RAINBOW_MODE_CLASS);
    }
  }, [theme]);

  const setTheme = (newTheme: ThemeMode) => {
    localStorage.setItem(STORAGE_KEY, newTheme);
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    setThemeState((current) => {
      const nextIndex = (THEME_CYCLE.indexOf(current) + 1) % THEME_CYCLE.length;
      const next = THEME_CYCLE[nextIndex];
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  };

  return {
    theme,
    isDarkMode: theme === 'dark',
    isRainbowMode: theme === 'rainbow',
    setTheme,
    toggleTheme,
  };
}
