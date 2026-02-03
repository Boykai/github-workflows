/**
 * Custom hook for managing theme (light/dark mode) with localStorage persistence.
 */

import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

const THEME_STORAGE_KEY = 'app-theme';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // Initialize from localStorage or default to 'light'
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return (stored === 'dark' || stored === 'light') ? stored : 'light';
  });

  useEffect(() => {
    // Apply theme to document root
    document.documentElement.setAttribute('data-theme', theme);
    // Persist to localStorage
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return { theme, toggleTheme };
}
