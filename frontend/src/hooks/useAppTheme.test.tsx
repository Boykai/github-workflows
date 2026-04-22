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

  it('should default to light theme when no stored preference', () => {
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
    expect(result.current.isRainbowMode).toBe(false);
  });

  it('should restore dark theme from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');

    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDarkMode).toBe(true);
    expect(result.current.isRainbowMode).toBe(false);
  });

  it('should restore rainbow theme from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'rainbow');

    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('rainbow');
    expect(result.current.isDarkMode).toBe(false);
    expect(result.current.isRainbowMode).toBe(true);
  });

  it('should cycle light → dark → rainbow → light via toggleTheme', () => {
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('light');

    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('dark');

    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('rainbow');

    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('light');
  });

  it('should apply dark-mode-active class when dark theme is set', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.setTheme('dark'); });

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(false);
  });

  it('should apply rainbow-mode-active class when rainbow theme is set', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.setTheme('rainbow'); });

    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });

  it('should remove theme classes when switching back to light', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.setTheme('light'); });

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(false);
  });

  it('should persist theme selection to localStorage', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.setTheme('rainbow'); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('rainbow');

    act(() => { result.current.setTheme('dark'); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');

    act(() => { result.current.setTheme('light'); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
  });

  it('should persist theme when toggling', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.toggleTheme(); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');

    act(() => { result.current.toggleTheme(); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('rainbow');

    act(() => { result.current.toggleTheme(); });
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
  });
});
