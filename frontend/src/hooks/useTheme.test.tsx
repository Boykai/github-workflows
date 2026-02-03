/**
 * Tests for useTheme hook
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { useTheme } from './useTheme';

describe('useTheme', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Clear all theme classes from document root
    document.documentElement.classList.remove('theme-light', 'theme-pink');
  });

  it('should initialize with light theme by default', () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('light');
  });

  it('should load saved theme from localStorage', () => {
    localStorage.setItem('app-theme', 'pink');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('pink');
  });

  it('should apply theme class to document root', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('pink');
    });

    expect(document.documentElement.classList.contains('theme-pink')).toBe(true);
    expect(result.current.theme).toBe('pink');
  });

  it('should persist theme to localStorage', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('pink');
    });

    expect(localStorage.getItem('app-theme')).toBe('pink');
  });

  it('should remove old theme class when changing themes', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('pink');
    });

    expect(document.documentElement.classList.contains('theme-pink')).toBe(true);

    act(() => {
      result.current.setTheme('light');
    });

    expect(document.documentElement.classList.contains('theme-pink')).toBe(false);
    expect(document.documentElement.classList.contains('theme-light')).toBe(false);
  });

  it('should handle invalid localStorage values gracefully', () => {
    localStorage.setItem('app-theme', 'invalid-theme');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('light');
  });
});
