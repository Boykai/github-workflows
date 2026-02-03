/**
 * Custom hook for managing app theme with localStorage persistence.
 */

import { useState, useEffect } from 'react';

export type Theme = 'light' | 'pink';

const THEME_STORAGE_KEY = 'app-theme';

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Load theme from localStorage or default to 'light'
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    return (savedTheme === 'pink' ? 'pink' : 'light') as Theme;
  });

  useEffect(() => {
    // Apply theme class to document root
    const root = document.documentElement;
    
    // Remove all theme classes
    root.classList.remove('theme-light', 'theme-pink');
    
    // Add the current theme class
    if (theme === 'pink') {
      root.classList.add('theme-pink');
    }
    
    // Persist theme to localStorage
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  return { theme, setTheme };
}
