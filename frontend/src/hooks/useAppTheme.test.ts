/**
 * Unit tests for useAppTheme hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAppTheme } from './useAppTheme';

// Shared store for localStorage mock
let localStore: Record<string, string> = {};

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn((key: string) => localStore[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { localStore[key] = value; }),
  removeItem: vi.fn((key: string) => { delete localStore[key]; }),
  clear: vi.fn(() => { localStore = {}; }),
};

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useAppTheme', () => {
  beforeEach(() => {
    // Reset store and re-apply implementations
    localStore = {};
    localStorageMock.getItem.mockImplementation((key: string) => localStore[key] ?? null);
    localStorageMock.setItem.mockImplementation((key: string, value: string) => { localStore[key] = value; });
    localStorageMock.removeItem.mockImplementation((key: string) => { delete localStore[key]; });
    localStorageMock.clear.mockImplementation(() => { localStore = {}; });
    // Reset html element classes
    document.documentElement.className = '';
  });

  afterEach(() => {
    document.documentElement.className = '';
  });

  it('should default to light theme when no stored preference', () => {
    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
    expect(result.current.isRainbowMode).toBe(false);
  });

  it('should restore dark theme from localStorage', () => {
    localStore['tech-connect-theme-mode'] = 'dark';

    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDarkMode).toBe(true);
    expect(result.current.isRainbowMode).toBe(false);
  });

  it('should restore rainbow theme from localStorage', () => {
    localStore['tech-connect-theme-mode'] = 'rainbow';

    const { result } = renderHook(() => useAppTheme());

    expect(result.current.theme).toBe('rainbow');
    expect(result.current.isDarkMode).toBe(false);
    expect(result.current.isRainbowMode).toBe(true);
  });

  it('should cycle from light to dark on first cycleTheme call', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.cycleTheme();
    });

    expect(result.current.theme).toBe('dark');
    expect(localStorageMock.setItem).toHaveBeenCalledWith('tech-connect-theme-mode', 'dark');
  });

  it('should cycle from dark to rainbow on second cycleTheme call', () => {
    localStore['tech-connect-theme-mode'] = 'dark';
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.cycleTheme();
    });

    expect(result.current.theme).toBe('rainbow');
    expect(localStorageMock.setItem).toHaveBeenCalledWith('tech-connect-theme-mode', 'rainbow');
  });

  it('should cycle from rainbow back to light on third cycleTheme call', () => {
    localStore['tech-connect-theme-mode'] = 'rainbow';
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.cycleTheme();
    });

    expect(result.current.theme).toBe('light');
    expect(localStorageMock.setItem).toHaveBeenCalledWith('tech-connect-theme-mode', 'light');
  });

  it('should apply dark-mode-active class to html element in dark mode', () => {
    localStore['tech-connect-theme-mode'] = 'dark';
    renderHook(() => useAppTheme());

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(false);
  });

  it('should apply rainbow-mode-active class to html element in rainbow mode', () => {
    localStore['tech-connect-theme-mode'] = 'rainbow';
    renderHook(() => useAppTheme());

    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(true);
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });

  it('should remove theme classes from html element in light mode', () => {
    document.documentElement.classList.add('dark-mode-active');
    document.documentElement.classList.add('rainbow-mode-active');

    renderHook(() => useAppTheme());

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
    expect(document.documentElement.classList.contains('rainbow-mode-active')).toBe(false);
  });

  it('should expose toggleTheme as alias for cycleTheme', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('dark');
  });
});

