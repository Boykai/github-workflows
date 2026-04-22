/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';
const HALLOWEEN_MODE_CLASS = 'halloween-mode-active';

type ThemeMode = 'light' | 'dark' | 'halloween';

const THEME_CYCLE: ThemeMode[] = ['light', 'dark', 'halloween'];

export function useAppTheme() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'halloween' || stored === 'light') {
      return stored as ThemeMode;
    }
    return 'light';
  });

  useEffect(() => {
    const rootElement = document.documentElement;
    rootElement.classList.remove(DARK_MODE_CLASS, HALLOWEEN_MODE_CLASS);
    if (themeMode === 'dark') {
      rootElement.classList.add(DARK_MODE_CLASS);
    } else if (themeMode === 'halloween') {
      rootElement.classList.add(HALLOWEEN_MODE_CLASS);
    }
  }, [themeMode]);

  const toggleTheme = () => {
    setThemeMode((current) => {
      const currentIndex = THEME_CYCLE.indexOf(current);
      const nextMode = THEME_CYCLE[(currentIndex + 1) % THEME_CYCLE.length];
      localStorage.setItem(STORAGE_KEY, nextMode);
      return nextMode;
    });
  };

  return {
    isDarkMode: themeMode === 'dark',
    isHalloweenMode: themeMode === 'halloween',
    themeMode,
    toggleTheme,
  };
}
