/**
 * Unit tests for useAppTheme hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAppTheme, DARK_MODE_CLASS, WINDOWS_THEME_CLASS } from './useAppTheme';

const STORAGE_KEY = 'tech-connect-theme-mode';

describe('useAppTheme', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove(DARK_MODE_CLASS, WINDOWS_THEME_CLASS);
    vi.spyOn(Storage.prototype, 'setItem');
    vi.spyOn(Storage.prototype, 'getItem');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('defaults to light mode when no stored preference', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.themeMode).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(false);
    expect(document.documentElement.classList.contains(WINDOWS_THEME_CLASS)).toBe(false);
  });

  it('restores dark mode from localStorage', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('dark');
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.themeMode).toBe('dark');
    expect(result.current.isDarkMode).toBe(true);
  });

  it('restores windows theme from localStorage', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('windows');
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.themeMode).toBe('windows');
    expect(result.current.isDarkMode).toBe(false);
  });

  it('cycles light → dark → windows → light on toggleTheme', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.themeMode).toBe('light');

    act(() => result.current.toggleTheme());
    expect(result.current.themeMode).toBe('dark');

    act(() => result.current.toggleTheme());
    expect(result.current.themeMode).toBe('windows');

    act(() => result.current.toggleTheme());
    expect(result.current.themeMode).toBe('light');
  });

  it('persists theme to localStorage when toggled', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    const { result } = renderHook(() => useAppTheme());

    act(() => result.current.toggleTheme());
    expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'dark');

    act(() => result.current.toggleTheme());
    expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'windows');

    act(() => result.current.toggleTheme());
    expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'light');
  });

  it('applies dark-mode-active class when dark mode is active', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    const { result } = renderHook(() => useAppTheme());

    act(() => result.current.toggleTheme()); // → dark
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(true);
    expect(document.documentElement.classList.contains(WINDOWS_THEME_CLASS)).toBe(false);
  });

  it('applies windows-theme-active class when Windows theme is active', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    const { result } = renderHook(() => useAppTheme());

    act(() => result.current.toggleTheme()); // → dark
    act(() => result.current.toggleTheme()); // → windows
    expect(document.documentElement.classList.contains(WINDOWS_THEME_CLASS)).toBe(true);
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(false);
  });

  it('removes theme classes when returning to light mode', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('windows');
    const { result } = renderHook(() => useAppTheme());

    act(() => result.current.toggleTheme()); // windows → light
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(false);
    expect(document.documentElement.classList.contains(WINDOWS_THEME_CLASS)).toBe(false);
  });
});
