/**
 * Unit tests for useAppTheme hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAppTheme } from './useAppTheme';

const STORAGE_KEY = 'tech-connect-theme-mode';

// Minimal localStorage mock
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useAppTheme', () => {
  beforeEach(() => {
    localStorageMock.clear();
    document.documentElement.className = '';
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('starts with light mode when no preference is stored and date is not Halloween', () => {
    // A non-Halloween date
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(false);
    expect(result.current.isHalloweenMode).toBe(false);
  });

  it('auto-activates Halloween mode on October 31st when no preference is stored', () => {
    vi.setSystemTime(new Date('2026-10-31'));
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isHalloweenMode).toBe(true);
    expect(result.current.isDarkMode).toBe(false);
  });

  it('does not auto-activate Halloween mode when an explicit preference is stored', () => {
    vi.setSystemTime(new Date('2026-10-31'));
    localStorageMock.setItem(STORAGE_KEY, 'light');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isHalloweenMode).toBe(false);
  });

  it('restores dark mode from localStorage', () => {
    localStorageMock.setItem(STORAGE_KEY, 'dark');
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(true);
    expect(result.current.isHalloweenMode).toBe(false);
  });

  it('restores Halloween mode from localStorage', () => {
    localStorageMock.setItem(STORAGE_KEY, 'halloween');
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isHalloweenMode).toBe(true);
    expect(result.current.isDarkMode).toBe(false);
  });

  it('toggleTheme enables dark mode and adds the class', () => {
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    act(() => { result.current.toggleTheme(); });
    expect(result.current.isDarkMode).toBe(true);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
    expect(localStorageMock.getItem(STORAGE_KEY)).toBe('dark');
  });

  it('toggleTheme disables dark mode and removes the class', () => {
    localStorageMock.setItem(STORAGE_KEY, 'dark');
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    act(() => { result.current.toggleTheme(); });
    expect(result.current.isDarkMode).toBe(false);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(localStorageMock.getItem(STORAGE_KEY)).toBe('light');
  });

  it('toggleHalloweenMode enables Halloween mode and adds the class', () => {
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    act(() => { result.current.toggleHalloweenMode(); });
    expect(result.current.isHalloweenMode).toBe(true);
    expect(document.documentElement.classList.contains('halloween-mode-active')).toBe(true);
    expect(localStorageMock.getItem(STORAGE_KEY)).toBe('halloween');
  });

  it('toggleHalloweenMode disables Halloween mode and removes the class', () => {
    localStorageMock.setItem(STORAGE_KEY, 'halloween');
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    act(() => { result.current.toggleHalloweenMode(); });
    expect(result.current.isHalloweenMode).toBe(false);
    expect(document.documentElement.classList.contains('halloween-mode-active')).toBe(false);
    expect(localStorageMock.getItem(STORAGE_KEY)).toBe('light');
  });

  it('switching to dark mode disables Halloween mode', () => {
    localStorageMock.setItem(STORAGE_KEY, 'halloween');
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isHalloweenMode).toBe(true);
    act(() => { result.current.toggleTheme(); });
    expect(result.current.isDarkMode).toBe(true);
    expect(result.current.isHalloweenMode).toBe(false);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('halloween-mode-active')).toBe(false);
  });

  it('switching to Halloween mode disables dark mode', () => {
    localStorageMock.setItem(STORAGE_KEY, 'dark');
    vi.setSystemTime(new Date('2026-04-22'));
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(true);
    act(() => { result.current.toggleHalloweenMode(); });
    expect(result.current.isHalloweenMode).toBe(true);
    expect(result.current.isDarkMode).toBe(false);
    expect(document.documentElement.classList.contains('halloween-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });
});
