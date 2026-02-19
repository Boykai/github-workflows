/**
 * Unit tests for useAppTheme hook
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAppTheme } from './useAppTheme';

describe('useAppTheme', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.classList.remove('dark-mode-active');
  });

  it('should default to light mode when no localStorage value', () => {
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(false);
  });

  it('should read dark from localStorage on init', () => {
    localStorage.setItem('tech-connect-theme-mode', 'dark');
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(true);
  });

  it('should toggle dark mode and update localStorage', () => {
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(false);

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

  it('should apply dark-mode-active class to documentElement', () => {
    localStorage.setItem('tech-connect-theme-mode', 'dark');
    renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);
  });

  it('should remove dark-mode-active class when toggling to light', () => {
    localStorage.setItem('tech-connect-theme-mode', 'dark');
    const { result } = renderHook(() => useAppTheme());
    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(true);

    act(() => {
      result.current.toggleTheme();
    });

    expect(document.documentElement.classList.contains('dark-mode-active')).toBe(false);
  });
});
