/**
 * Custom hook for managing application theme preferences
 */

import { useState, useEffect } from 'react';

export type ThemeMode = 'light' | 'dark' | 'retro';

const STORAGE_KEY = 'tech-connect-theme-mode';
const DARK_MODE_CLASS = 'dark-mode-active';
const RETRO_MODE_CLASS = 'retro-mode-active';
const RETRO_PREVIEW_CLASS = 'retro-preview-active';

function applyClasses(mode: ThemeMode, previewing: boolean) {
  const root = document.documentElement;
  root.classList.remove(DARK_MODE_CLASS, RETRO_MODE_CLASS, RETRO_PREVIEW_CLASS);
  if (mode === 'dark') root.classList.add(DARK_MODE_CLASS);
  else if (mode === 'retro') root.classList.add(RETRO_MODE_CLASS);
  if (previewing && mode !== 'retro') root.classList.add(RETRO_PREVIEW_CLASS);
}

export function useAppTheme() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'retro') return stored;
    return 'light';
  });

  const [isPreviewingRetro, setIsPreviewingRetro] = useState(false);

  const isDarkMode = themeMode === 'dark';
  const isRetroMode = themeMode === 'retro';

  useEffect(() => {
    applyClasses(themeMode, isPreviewingRetro);
  }, [themeMode, isPreviewingRetro]);

  const toggleTheme = () => {
    setIsPreviewingRetro(false);
    setThemeMode((current) => {
      const next: ThemeMode =
        current === 'light' ? 'dark' : current === 'dark' ? 'retro' : 'light';
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  };

  const setTheme = (mode: ThemeMode) => {
    localStorage.setItem(STORAGE_KEY, mode);
    setIsPreviewingRetro(false);
    setThemeMode(mode);
  };

  const previewRetroTheme = () => {
    if (themeMode !== 'retro') {
      setIsPreviewingRetro(true);
    }
  };

  const cancelRetroPreview = () => {
    setIsPreviewingRetro(false);
  };

  return {
    isDarkMode,
    isRetroMode,
    themeMode,
    isPreviewingRetro,
    toggleTheme,
    setTheme,
    previewRetroTheme,
    cancelRetroPreview,
  };
}
