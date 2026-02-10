/**
 * Tests for useTheme hook
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';

describe('useTheme', () => {
  const STORAGE_KEY = 'tech-connect-theme-mode';
  const DARK_MODE_CLASS = 'dark-mode-active';

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Remove dark mode class
    document.documentElement.classList.remove(DARK_MODE_CLASS);
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove(DARK_MODE_CLASS);
  });

  it('should initialize with light theme by default', () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('light');
  });

  it('should initialize with stored theme preference', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('dark');
  });

  it('should toggle theme from light to dark', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('dark');
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(true);
  });

  it('should toggle theme from dark to light', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('light');
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(false);
  });

  it('should persist theme preference to localStorage', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');
  });

  it('should apply dark mode class to document when theme is dark', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(true);
  });

  it('should remove dark mode class when theme is light', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');
    document.documentElement.classList.add(DARK_MODE_CLASS);
    
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(document.documentElement.classList.contains(DARK_MODE_CLASS)).toBe(false);
  });
});
