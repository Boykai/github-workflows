/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

export type AppTheme = 'light' | 'dark' | 'spooky-ghost';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';
const SPOOKY_GHOST_CLASS = 'spooky-ghost-active';

const THEME_CYCLE: AppTheme[] = ['light', 'dark', 'spooky-ghost'];

function getStoredTheme(): AppTheme {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (THEME_CYCLE.includes(stored as AppTheme)) {
    return stored as AppTheme;
  }
  return 'light';
}

export function useAppTheme() {
  const [theme, setThemeState] = useState<AppTheme>(getStoredTheme);

  useEffect(() => {
    const rootElement = document.documentElement;
    rootElement.classList.remove(DARK_MODE_CLASS, SPOOKY_GHOST_CLASS);
    if (theme === 'dark') {
      rootElement.classList.add(DARK_MODE_CLASS);
    } else if (theme === 'spooky-ghost') {
      rootElement.classList.add(SPOOKY_GHOST_CLASS);
    }
  }, [theme]);

  const toggleTheme = () => {
    setThemeState((current) => {
      const currentIndex = THEME_CYCLE.indexOf(current);
      const nextTheme = THEME_CYCLE[(currentIndex + 1) % THEME_CYCLE.length];
      localStorage.setItem(STORAGE_KEY, nextTheme);
      return nextTheme;
    });
  };

  const isDarkMode = theme === 'dark';
  const isSpookyGhost = theme === 'spooky-ghost';

  return {
    theme,
    isDarkMode,
    isSpookyGhost,
    toggleTheme,
  };
}
