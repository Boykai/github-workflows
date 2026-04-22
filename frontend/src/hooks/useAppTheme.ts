/**
 * Custom hook for managing application theme preferences.
 * Supports three themes: 'light', 'dark', and 'windows' (Windows Modern).
 */

import { useState, useEffect, useCallback } from 'react';

export type ThemeMode = 'light' | 'dark' | 'windows';

const STORAGE_KEY = 'tech-connect-theme-mode';
const THEME_ORDER: ThemeMode[] = ['light', 'dark', 'windows'];

const THEME_CLASSES: Record<ThemeMode, string | null> = {
  light: null,
  dark: 'dark-mode-active',
  windows: 'windows-theme-active',
};

const TRANSITION_CLASS = 'theme-transitioning';
const TRANSITION_DURATION_MS = 300;

function resolveInitialTheme(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'dark' || stored === 'windows' || stored === 'light') {
    return stored;
  }
  return 'light';
}

export function useAppTheme() {
  const [theme, setTheme] = useState<ThemeMode>(resolveInitialTheme);

  useEffect(() => {
    const rootElement = document.documentElement;
    rootElement.classList.remove('dark-mode-active', 'windows-theme-active');
    const cls = THEME_CLASSES[theme];
    if (cls) {
      rootElement.classList.add(cls);
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    const rootElement = document.documentElement;
    rootElement.classList.add(TRANSITION_CLASS);

    setTheme((current) => {
      const nextIndex = (THEME_ORDER.indexOf(current) + 1) % THEME_ORDER.length;
      const next = THEME_ORDER[nextIndex];
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });

    setTimeout(() => {
      rootElement.classList.remove(TRANSITION_CLASS);
    }, TRANSITION_DURATION_MS);
  }, []);

  return {
    theme,
    isDarkMode: theme === 'dark',
    toggleTheme,
  };
}
