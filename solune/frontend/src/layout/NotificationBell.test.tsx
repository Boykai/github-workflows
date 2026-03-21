/**
 * Tests for NotificationBell — verifies RAF-throttled scroll positioning.
 *
 * Scroll and resize handlers previously called getBoundingClientRect() and
 * setState() directly on every event, causing layout thrashing. The fix wraps
 * these handlers in requestAnimationFrame to batch updates to once per frame.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { NotificationBell } from './NotificationBell';

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('NotificationBell — scroll handler throttling', () => {
  let rafSpy: ReturnType<typeof vi.spyOn>;
  let cafSpy: ReturnType<typeof vi.spyOn>;
  const rafCallbacks: FrameRequestCallback[] = [];
  let rafIdCounter = 1;

  beforeEach(() => {
    rafCallbacks.length = 0;
    rafIdCounter = 1;
    rafSpy = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      rafCallbacks.push(cb);
      return rafIdCounter++;
    });
    cafSpy = vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => {});
  });

  afterEach(() => {
    rafSpy.mockRestore();
    cafSpy.mockRestore();
  });

  function flushRAF() {
    act(() => {
      const cbs = [...rafCallbacks];
      rafCallbacks.length = 0;
      cbs.forEach((cb) => cb(performance.now()));
    });
  }

  it('uses requestAnimationFrame to throttle scroll-driven position updates', () => {
    renderWithRouter(<NotificationBell notifications={[]} unreadCount={0} onMarkAllRead={vi.fn()} />);

    // Open the dropdown
    fireEvent.click(screen.getByRole('button', { name: /Notifications/i }));

    // Clear any RAFs triggered by initial positioning
    rafSpy.mockClear();
    flushRAF();

    // Dispatch multiple scroll events rapidly
    act(() => {
      fireEvent.scroll(window);
      fireEvent.scroll(window);
      fireEvent.scroll(window);
    });

    // Only one RAF should be scheduled (subsequent events are coalesced)
    expect(rafSpy).toHaveBeenCalledTimes(1);

    // Flush the RAF callback
    flushRAF();

    // Now a new scroll event should schedule a new RAF
    rafSpy.mockClear();
    act(() => {
      fireEvent.scroll(window);
    });
    expect(rafSpy).toHaveBeenCalledTimes(1);
  });

  it('cancels pending RAF on dropdown close', () => {
    renderWithRouter(<NotificationBell notifications={[]} unreadCount={0} onMarkAllRead={vi.fn()} />);

    const button = screen.getByRole('button', { name: /Notifications/i });

    // Open the dropdown
    fireEvent.click(button);

    // Trigger a scroll event to schedule a RAF
    act(() => {
      fireEvent.scroll(window);
    });

    cafSpy.mockClear();

    // Close the dropdown — pending RAF should be cancelled during cleanup
    fireEvent.click(button);

    expect(cafSpy).toHaveBeenCalled();
  });
});
