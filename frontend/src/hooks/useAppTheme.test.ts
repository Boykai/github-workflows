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
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    document.documentElement.className = '';
    localStorage.clear();
  });

  it('should default to light theme when no stored preference', () => {
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.theme).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
  });

  it('should restore dark theme from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.theme).toBe('dark');
    expect(result.current.isDarkMode).toBe(true);
  });

  it('should restore windows theme from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'windows');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.theme).toBe('windows');
    expect(result.current.isDarkMode).toBe(false);
  });

  it('should apply dark-mode-active class when theme is dark', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('windows-theme-active')).toBe(false);
  });

  it('should apply windows-theme-active class when theme is windows', () => {
    localStorage.setItem(STORAGE_KEY, 'windows');
    renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('windows-theme-active')).toBe(true);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });

  it('should not apply any theme class when theme is light', () => {
    renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('windows-theme-active')).toBe(false);
  });

  it('should cycle light -> dark -> windows -> light on toggleTheme', () => {
    const { result } = renderHook(() => useAppTheme());

    // light -> dark
    act(() => {
      result.current.toggleTheme();
      vi.runAllTimers();
    });
    expect(result.current.theme).toBe('dark');
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');

    // dark -> windows
    act(() => {
      result.current.toggleTheme();
      vi.runAllTimers();
    });
    expect(result.current.theme).toBe('windows');
    expect(localStorage.getItem(STORAGE_KEY)).toBe('windows');

    // windows -> light
    act(() => {
      result.current.toggleTheme();
      vi.runAllTimers();
    });
    expect(result.current.theme).toBe('light');
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
  });

  it('should add theme-transitioning class during toggle and remove it after 300ms', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(false);
  });

  it('should remove stale theme class when switching themes', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    const { result } = renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);

    // dark -> windows
    act(() => {
      result.current.toggleTheme();
      vi.runAllTimers();
    });
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('windows-theme-active')).toBe(true);
  });
});
