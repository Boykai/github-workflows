/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

export type ThemeMode = 'light' | 'dark' | 'windows';

const STORAGE_KEY = 'tech-connect-theme-mode';
export const DARK_MODE_CLASS = 'dark-mode-active';
export const WINDOWS_THEME_CLASS = 'windows-theme-active';

function applyTheme(mode: ThemeMode) {
  const root = document.documentElement;
  root.classList.remove(DARK_MODE_CLASS, WINDOWS_THEME_CLASS);
  if (mode === 'dark') root.classList.add(DARK_MODE_CLASS);
  if (mode === 'windows') root.classList.add(WINDOWS_THEME_CLASS);
}

export function useAppTheme() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'windows') return stored;
    return 'light';
  });

  useEffect(() => {
    applyTheme(themeMode);
  }, [themeMode]);

  const toggleTheme = () => {
    setThemeMode((current) => {
      const next: ThemeMode =
        current === 'light' ? 'dark' : current === 'dark' ? 'windows' : 'light';
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  };

  // Legacy boolean kept for backwards-compatibility with existing consumers
  const isDarkMode = themeMode === 'dark';

  return {
    themeMode,
    isDarkMode,
    toggleTheme,
  };
}
