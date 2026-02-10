/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';

export function useAppTheme() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'dark';
  });

  useEffect(() => {
    const rootElement = document.documentElement;
    if (isDarkMode) {
      rootElement.classList.add(DARK_MODE_CLASS);
    } else {
      rootElement.classList.remove(DARK_MODE_CLASS);
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode((current) => {
      const newMode = !current;
      localStorage.setItem(STORAGE_KEY, newMode ? 'dark' : 'light');
      return newMode;
    });
  };

  return {
    isDarkMode,
    toggleTheme,
  };
}
