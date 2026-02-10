/**
 * Tests for ThemeToggle component
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThemeToggle } from './ThemeToggle';

// Mock the useTheme hook
vi.mock('@/hooks/useTheme', () => ({
  useTheme: vi.fn(),
}));

import { useTheme } from '@/hooks/useTheme';

describe('ThemeToggle', () => {
  const mockToggleTheme = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should render moon icon when theme is light', () => {
    vi.mocked(useTheme).mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: /switch to dark theme/i });
    expect(button).toBeTruthy();
    expect(button.textContent).toBe('🌙');
  });

  it('should render sun icon when theme is dark', () => {
    vi.mocked(useTheme).mockReturnValue({
      theme: 'dark',
      toggleTheme: mockToggleTheme,
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: /switch to light theme/i });
    expect(button).toBeTruthy();
    expect(button.textContent).toBe('☀️');
  });

  it('should call toggleTheme when clicked', () => {
    vi.mocked(useTheme).mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    button.click();
    
    expect(mockToggleTheme).toHaveBeenCalledTimes(1);
  });

  it('should have correct aria-label for light theme', () => {
    vi.mocked(useTheme).mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-label')).toBe('Switch to dark theme');
  });

  it('should have correct aria-label for dark theme', () => {
    vi.mocked(useTheme).mockReturnValue({
      theme: 'dark',
      toggleTheme: mockToggleTheme,
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-label')).toBe('Switch to light theme');
  });
});
