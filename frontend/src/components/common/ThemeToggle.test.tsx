/**
 * Tests for ThemeToggle component.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ThemeToggle } from './ThemeToggle';

describe('ThemeToggle', () => {
  it('should render sun icon in light mode', () => {
    const onToggle = vi.fn();
    render(<ThemeToggle theme="light" onToggle={onToggle} />);

    const button = screen.getByRole('button', { name: /switch to dark theme/i });
    expect(button).toBeDefined();
  });

  it('should render moon icon in dark mode', () => {
    const onToggle = vi.fn();
    render(<ThemeToggle theme="dark" onToggle={onToggle} />);

    const button = screen.getByRole('button', { name: /switch to light theme/i });
    expect(button).toBeDefined();
  });

  it('should call onToggle when clicked', () => {
    const onToggle = vi.fn();
    render(<ThemeToggle theme="light" onToggle={onToggle} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('should have correct aria-label for light theme', () => {
    const onToggle = vi.fn();
    render(<ThemeToggle theme="light" onToggle={onToggle} />);

    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-label')).toBe('Switch to dark theme');
  });

  it('should have correct aria-label for dark theme', () => {
    const onToggle = vi.fn();
    render(<ThemeToggle theme="dark" onToggle={onToggle} />);

    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-label')).toBe('Switch to light theme');
  });
});
