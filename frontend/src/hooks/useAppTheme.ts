/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';
const HALLOWEEN_MODE_CLASS = 'halloween-mode-active';

export function useAppTheme() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'dark';
  });

  const [isHalloweenMode, setIsHalloweenMode] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) === 'halloween';
  });

  useEffect(() => {
    const rootElement = document.documentElement;
    if (isHalloweenMode) {
      rootElement.classList.remove(DARK_MODE_CLASS);
      rootElement.classList.add(HALLOWEEN_MODE_CLASS);
    } else if (isDarkMode) {
      rootElement.classList.remove(HALLOWEEN_MODE_CLASS);
      rootElement.classList.add(DARK_MODE_CLASS);
    } else {
      rootElement.classList.remove(DARK_MODE_CLASS);
      rootElement.classList.remove(HALLOWEEN_MODE_CLASS);
    }
  }, [isDarkMode, isHalloweenMode]);

  const toggleTheme = () => {
    setIsDarkMode((current) => {
      const newMode = !current;
      if (newMode) {
        setIsHalloweenMode(false);
        localStorage.setItem(STORAGE_KEY, 'dark');
      } else {
        localStorage.setItem(STORAGE_KEY, 'light');
      }
      return newMode;
    });
  };

  const toggleHalloween = () => {
    setIsHalloweenMode((current) => {
      const newMode = !current;
      if (newMode) {
        setIsDarkMode(false);
        localStorage.setItem(STORAGE_KEY, 'halloween');
      } else {
        localStorage.setItem(STORAGE_KEY, 'light');
      }
      return newMode;
    });
  };

  return {
    isDarkMode,
    isHalloweenMode,
    toggleTheme,
    toggleHalloween,
  };
}
