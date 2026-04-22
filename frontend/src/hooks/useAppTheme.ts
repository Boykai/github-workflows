/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';
const RAINBOW_MODE_CLASS = 'rainbow-mode-active';

export type ThemeMode = 'light' | 'dark' | 'rainbow';

const THEME_CYCLE: ThemeMode[] = ['light', 'dark', 'rainbow'];

function getInitialTheme(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'dark' || stored === 'rainbow' || stored === 'light') {
    return stored;
  }
  return 'light';
}

export function useAppTheme() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(getInitialTheme);

  useEffect(() => {
    const rootElement = document.documentElement;
    rootElement.classList.remove(DARK_MODE_CLASS, RAINBOW_MODE_CLASS);
    if (themeMode === 'dark') {
      rootElement.classList.add(DARK_MODE_CLASS);
    } else if (themeMode === 'rainbow') {
      rootElement.classList.add(RAINBOW_MODE_CLASS);
    }
  }, [themeMode]);

  const cycleTheme = () => {
    setThemeMode((current) => {
      const currentIndex = THEME_CYCLE.indexOf(current);
      const next = THEME_CYCLE[(currentIndex + 1) % THEME_CYCLE.length];
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  };

  return {
    themeMode,
    isDarkMode: themeMode === 'dark',
    cycleTheme,
  };
}
