/**
 * Tests for useTheme hook
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';

describe('useTheme', () => {
  const THEME_STORAGE_KEY = 'tech-connect-theme-mode';
  const THEME_CLASS = 'dark-mode-active';

  beforeEach(() => {
    // Clear localStorage and reset DOM before each test
    localStorage.clear();
    document.documentElement.classList.remove(THEME_CLASS);
  });

  afterEach(() => {
    // Clean up after each test
    localStorage.clear();
    document.documentElement.classList.remove(THEME_CLASS);
  });

  it('should default to light theme', () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('light');
    expect(result.current.isDark).toBe(false);
    expect(document.documentElement.classList.contains(THEME_CLASS)).toBe(false);
  });

  it('should load theme from localStorage', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark');

    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
    expect(document.documentElement.classList.contains(THEME_CLASS)).toBe(true);
  });

  it('should toggle theme from light to dark', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
    expect(document.documentElement.classList.contains(THEME_CLASS)).toBe(true);
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');
  });

  it('should toggle theme from dark to light', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark');

    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('light');
    expect(result.current.isDark).toBe(false);
    expect(document.documentElement.classList.contains(THEME_CLASS)).toBe(false);
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light');
  });

  it('should persist theme to localStorage', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');

    act(() => {
      result.current.toggleTheme();
    });

    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light');
  });

  it('should apply dark-mode-active class when dark theme is active', () => {
    const { result } = renderHook(() => useTheme());

    expect(document.documentElement.classList.contains(THEME_CLASS)).toBe(false);

    act(() => {
      result.current.toggleTheme();
    });

    expect(document.documentElement.classList.contains(THEME_CLASS)).toBe(true);
  });
});
