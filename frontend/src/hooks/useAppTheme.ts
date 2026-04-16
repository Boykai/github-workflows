/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';
const PRIDE_MODE_CLASS = 'pride-mode-active';

/** Returns true when the current month is June (Pride Month). */
export function isPrideMonth(date: Date = new Date()): boolean {
  return date.getMonth() === 5; // Month is 0-indexed; 5 = June
}

export function useAppTheme() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'dark';
  });

  const [isPride] = useState(() => isPrideMonth());

  useEffect(() => {
    const rootElement = document.documentElement;
    if (isDarkMode) {
      rootElement.classList.add(DARK_MODE_CLASS);
    } else {
      rootElement.classList.remove(DARK_MODE_CLASS);
    }
  }, [isDarkMode]);

  useEffect(() => {
    const rootElement = document.documentElement;
    if (isPride) {
      rootElement.classList.add(PRIDE_MODE_CLASS);
    } else {
      rootElement.classList.remove(PRIDE_MODE_CLASS);
    }
    return () => {
      rootElement.classList.remove(PRIDE_MODE_CLASS);
    };
  }, [isPride]);

  const toggleTheme = () => {
    setIsDarkMode((current) => {
      const newMode = !current;
      localStorage.setItem(STORAGE_KEY, newMode ? 'dark' : 'light');
      return newMode;
    });
  };

  return {
    isDarkMode,
    isPrideMonth: isPride,
    toggleTheme,
  };
}
