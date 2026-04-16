/**
 * Unit tests for useAppTheme hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAppTheme, isPrideMonth } from './useAppTheme';

// ---------------------------------------------------------------------------
// isPrideMonth helper
// ---------------------------------------------------------------------------

describe('isPrideMonth', () => {
  it('returns true when the date is in June', () => {
    expect(isPrideMonth(new Date(2026, 5, 1))).toBe(true);  // June 1
    expect(isPrideMonth(new Date(2026, 5, 15))).toBe(true); // June 15
    expect(isPrideMonth(new Date(2026, 5, 30))).toBe(true); // June 30
  });

  it('returns false for every other month', () => {
    const nonJuneMonths = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11];
    nonJuneMonths.forEach((month) => {
      expect(isPrideMonth(new Date(2026, month, 15))).toBe(false);
    });
  });
});

// ---------------------------------------------------------------------------
// useAppTheme hook
// ---------------------------------------------------------------------------

describe('useAppTheme', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = '';
  });

  afterEach(() => {
    vi.useRealTimers();
    document.documentElement.className = '';
  });

  it('starts in light mode when no stored preference exists', () => {
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(false);
  });

  it('starts in dark mode when stored preference is "dark"', () => {
    localStorage.setItem('tech-connect-theme-mode', 'dark');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(true);
  });

  it('toggles dark mode and persists the preference', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.isDarkMode).toBe(true);
    expect(localStorage.getItem('tech-connect-theme-mode')).toBe('dark');

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.isDarkMode).toBe(false);
    expect(localStorage.getItem('tech-connect-theme-mode')).toBe('light');
  });

  it('adds dark-mode-active class to html element when dark mode is on', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);

    act(() => {
      result.current.toggleTheme();
    });

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });

  it('detects Pride Month (June) and exposes isPrideMonth = true', () => {
    // Freeze time to a June date
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 5, 15)); // June 15, 2026

    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isPrideMonth).toBe(true);
  });

  it('adds pride-mode-active class to html element during June', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 5, 1)); // June 1, 2026

    renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('pride-mode-active')).toBe(true);
  });

  it('does not add pride-mode-active class outside of June', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 4, 31)); // May 31, 2026

    renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('pride-mode-active')).toBe(false);
  });

  it('exposes isPrideMonth = false outside of June', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 1)); // July 1, 2026

    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isPrideMonth).toBe(false);
  });
});
