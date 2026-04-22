/**
 * Unit tests for useAppTheme hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAppTheme } from './useAppTheme';

const STORAGE_KEY = 'tech-connect-theme-mode';

let store: Record<string, string> = {};

const localStorageMock = {
  getItem: vi.fn((key: string) => store[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
  removeItem: vi.fn((key: string) => { delete store[key]; }),
  clear: vi.fn(() => { store = {}; }),
};

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useAppTheme', () => {
  beforeEach(() => {
    store = {};
    // Re-install implementations so stale mockReturnValue calls don't bleed across tests
    localStorageMock.getItem.mockImplementation((key: string) => store[key] ?? null);
    localStorageMock.setItem.mockImplementation((key: string, value: string) => { store[key] = value; });
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
    document.documentElement.className = '';
  });

  afterEach(() => {
    document.documentElement.className = '';
  });

  it('should default to light theme when no stored value', () => {
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
    expect(result.current.isSpookyGhost).toBe(false);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('spooky-ghost-active')).toBe(false);
  });

  it('should restore dark theme from localStorage', () => {
    store[STORAGE_KEY] = 'dark';

    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDarkMode).toBe(true);
    expect(result.current.isSpookyGhost).toBe(false);
  });

  it('should restore spooky-ghost theme from localStorage', () => {
    store[STORAGE_KEY] = 'spooky-ghost';

    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('spooky-ghost');
    expect(result.current.isDarkMode).toBe(false);
    expect(result.current.isSpookyGhost).toBe(true);
  });

  it('should cycle light → dark → spooky-ghost → light on toggleTheme', () => {
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('light');

    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('dark');

    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('spooky-ghost');

    act(() => { result.current.toggleTheme(); });
    expect(result.current.theme).toBe('light');
  });

  it('should persist theme to localStorage when toggling', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.toggleTheme(); });
    expect(localStorageMock.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'dark');

    act(() => { result.current.toggleTheme(); });
    expect(localStorageMock.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'spooky-ghost');

    act(() => { result.current.toggleTheme(); });
    expect(localStorageMock.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'light');
  });

  it('should apply dark-mode-active class when dark theme is active', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.toggleTheme(); });

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('spooky-ghost-active')).toBe(false);
  });

  it('should apply spooky-ghost-active class when spooky-ghost theme is active', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.toggleTheme(); }); // → dark
    act(() => { result.current.toggleTheme(); }); // → spooky-ghost

    expect(document.documentElement.classList.contains('spooky-ghost-active')).toBe(true);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });

  it('should remove theme classes when switching back to light', () => {
    store[STORAGE_KEY] = 'spooky-ghost';
    const { result } = renderHook(() => useAppTheme());

    act(() => { result.current.toggleTheme(); }); // → light

    expect(document.documentElement.classList.contains('spooky-ghost-active')).toBe(false);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });
});
