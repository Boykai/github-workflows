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
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'rainbow') return stored;
    return 'light';
  });

  useEffect(() => {
    const rootElement = document.documentElement;
    rootElement.classList.toggle(DARK_MODE_CLASS, theme === 'dark');
    rootElement.classList.toggle(RAINBOW_MODE_CLASS, theme === 'rainbow');
  }, [theme]);

  const cycleTheme = () => {
    setTheme((current) => {
      const currentIndex = THEME_CYCLE.indexOf(current);
      const next = THEME_CYCLE[(currentIndex + 1) % THEME_CYCLE.length];
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  };

  return {
    theme,
    isDarkMode: theme === 'dark',
    isRainbowMode: theme === 'rainbow',
    cycleTheme,
    toggleTheme: cycleTheme,
  };
}
