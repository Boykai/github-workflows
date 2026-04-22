/**
 * Unit tests for useAppTheme hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAppTheme } from './useAppTheme';

const STORAGE_KEY = 'tech-connect-theme-mode';

describe('useAppTheme', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = '';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('defaults to light theme when no stored value', () => {
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.themeMode).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(false);
  });

  it('initialises to dark theme from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.themeMode).toBe('dark');
    expect(result.current.isDarkMode).toBe(true);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
  });

  it('initialises to rainbow theme from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'rainbow');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.themeMode).toBe('rainbow');
    expect(result.current.isDarkMode).toBe(false);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(true);
  });

  it('cycles light → dark → rainbow → light', () => {
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.themeMode).toBe('light');

    act(() => { result.current.cycleTheme(); });
    expect(result.current.themeMode).toBe('dark');
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(false);

    act(() => { result.current.cycleTheme(); });
    expect(result.current.themeMode).toBe('rainbow');
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(true);

    act(() => { result.current.cycleTheme(); });
    expect(result.current.themeMode).toBe('light');
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(false);
  });

  it('persists the chosen theme in localStorage', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.cycleTheme(); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');

    act(() => { result.current.cycleTheme(); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('rainbow');

    act(() => { result.current.cycleTheme(); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
  });

  it('treats unknown stored values as light theme', () => {
    localStorage.setItem(STORAGE_KEY, 'unknown-value');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.themeMode).toBe('light');
  });
});
