/**
 * Unit tests for DateTimeDisplay component
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DateTimeDisplay } from './DateTimeDisplay';

describe('DateTimeDisplay', () => {
  beforeEach(() => {
    // Use fake timers
    vi.useFakeTimers();
    // Set a fixed date for consistent testing
    vi.setSystemTime(new Date('2026-02-03T14:30:45'));
  });

  afterEach(() => {
    // Restore real timers
    vi.useRealTimers();
  });

  it('should render the current date in YYYY-MM-DD format', () => {
    render(<DateTimeDisplay />);
    
    // Check for date display
    const dateElement = screen.getByText('2026-02-03');
    expect(dateElement).toBeDefined();
  });

  it('should render the current time in HH:mm:ss format', () => {
    render(<DateTimeDisplay />);
    
    // Check for time display
    const timeElement = screen.getByText('14:30:45');
    expect(timeElement).toBeDefined();
  });

  it('should update time every second', async () => {
    const { rerender } = render(<DateTimeDisplay />);
    
    // Initial time
    expect(screen.getByText('14:30:45')).toBeDefined();
    
    // Advance time by 1 second
    vi.advanceTimersByTime(1000);
    
    // Force re-render to see updated time
    rerender(<DateTimeDisplay />);
    
    // Check updated time
    expect(screen.getByText('14:30:46')).toBeDefined();
    
    // Advance time by another second
    vi.advanceTimersByTime(1000);
    
    // Force re-render
    rerender(<DateTimeDisplay />);
    
    // Check updated time again
    expect(screen.getByText('14:30:47')).toBeDefined();
  });

  it('should have proper ARIA attributes for accessibility', () => {
    render(<DateTimeDisplay />);
    
    // Check for aria-live attribute
    const container = screen.getByLabelText(/current date/i);
    expect(container).toBeDefined();
    
    // Check for time element with dateTime attribute
    const timeElement = screen.getByText('14:30:45').closest('time');
    expect(timeElement).toBeTruthy();
    expect(timeElement?.getAttribute('dateTime')).toBeTruthy();
  });

  it('should format date correctly with padding', () => {
    // Test with single digit date
    vi.setSystemTime(new Date('2026-01-05T08:05:02'));
    
    render(<DateTimeDisplay />);
    
    expect(screen.getByText('2026-01-05')).toBeDefined();
    expect(screen.getByText('08:05:02')).toBeDefined();
  });

  it('should include a separator between date and time', () => {
    render(<DateTimeDisplay />);
    
    const separator = screen.getByText('|');
    expect(separator).toBeDefined();
    expect(separator.getAttribute('aria-hidden')).toBe('true');
  });

  it('should cleanup interval on unmount', () => {
    const { unmount } = render(<DateTimeDisplay />);
    
    // Spy on clearInterval
    const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval');
    
    // Unmount component
    unmount();
    
    // Check that clearInterval was called
    expect(clearIntervalSpy).toHaveBeenCalled();
    
    clearIntervalSpy.mockRestore();
  });
});
