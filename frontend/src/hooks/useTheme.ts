/**
 * Custom hook for managing theme (light/dark mode) state.
 */

import { useEffect, useState } from 'react';

const THEME_STORAGE_KEY = 'tech-connect-theme-mode';
const THEME_CLASS = 'dark-mode-active';

type Theme = 'light' | 'dark';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // Get theme from localStorage or default to 'light'
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return (stored === 'dark' || stored === 'light') ? stored : 'light';
  });

  useEffect(() => {
    // Apply theme class to html element
    const html = document.documentElement;
    if (theme === 'dark') {
      html.classList.add(THEME_CLASS);
    } else {
      html.classList.remove(THEME_CLASS);
    }

    // Persist theme to localStorage
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return {
    theme,
    toggleTheme,
    isDark: theme === 'dark',
  };
}
