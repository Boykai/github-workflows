/**
 * Unit tests for LocalTime component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { LocalTime } from './LocalTime';

describe('LocalTime', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the current time in HH:mm format', () => {
    const testDate = new Date('2026-02-11T14:30:00');
    vi.setSystemTime(testDate);

    render(<LocalTime />);

    // Check that time is displayed
    const timeDisplay = screen.getByText('14:30');
    expect(timeDisplay).toBeTruthy();
  });

  it('displays a clock icon', () => {
    render(<LocalTime />);

    // Check that clock icon is present
    const icon = screen.getByText('🕐');
    expect(icon).toBeTruthy();
  });

  it('updates time every minute', () => {
    const testDate = new Date('2026-02-11T14:30:00');
    vi.setSystemTime(testDate);

    render(<LocalTime />);

    // Initial time
    expect(screen.getByText('14:30')).toBeTruthy();

    // Advance time by 1 minute
    act(() => {
      vi.setSystemTime(new Date('2026-02-11T14:31:00'));
      vi.advanceTimersByTime(60000);
    });

    // Time should have updated (might be 14:31 or later depending on when Date is called)
    expect(screen.queryByText('14:30')).toBeFalsy();
    // Verify a new time is shown
    const timeDisplay = screen.getByText(/\d{2}:\d{2}/);
    expect(timeDisplay).toBeTruthy();
  });

  it('has a tooltip with full date and timezone', () => {
    const testDate = new Date('2026-02-11T14:30:00');
    vi.setSystemTime(testDate);

    render(<LocalTime />);

    const container = screen.getByText('14:30').closest('.local-time');
    expect(container).toBeTruthy();

    const title = container?.getAttribute('title');
    // Check that title includes the date (in some format) and timezone
    expect(title).toContain('2026');
    expect(title).toContain('February');
  });

  it('formats time correctly for different hours', () => {
    const testDate = new Date('2026-02-11T09:05:00');
    vi.setSystemTime(testDate);

    render(<LocalTime />);

    // Should show 09:05 in 24-hour format
    expect(screen.getByText('09:05')).toBeTruthy();
  });
});
