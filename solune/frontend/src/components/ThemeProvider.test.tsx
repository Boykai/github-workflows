/**
 * Integration tests for ThemeProvider theme switching and persistence.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, userEvent, fireEvent, act } from '@/test/test-utils';
import { ThemeProvider, useTheme } from './ThemeProvider';

/** Helper component that exposes theme context for testing. */
function ThemeConsumer() {
  const { theme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="current-theme">{theme}</span>
      <button onClick={() => setTheme('light')}>Set Light</button>
      <button onClick={() => setTheme('dark')}>Set Dark</button>
      <button onClick={() => setTheme('system')}>Set System</button>
    </div>
  );
}

describe('ThemeProvider', () => {
  let matchMediaMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('light', 'dark');

    matchMediaMock = vi.fn().mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    Object.defineProperty(window, 'matchMedia', { value: matchMediaMock, writable: true });
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('light', 'dark', 'theme-transitioning');
  });

  it('defaults to system theme', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('current-theme')).toHaveTextContent('system');
  });

  it('applies light class when system prefers light', () => {
    matchMediaMock.mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('applies dark class when system prefers dark', () => {
    matchMediaMock.mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('switches from system to dark on setTheme', async () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Set Dark' }));
    expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('switches from dark to light', async () => {
    render(
      <ThemeProvider defaultTheme="dark">
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    await userEvent.setup().click(screen.getByRole('button', { name: 'Set Light' }));
    expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('persists theme to localStorage on change', async () => {
    render(
      <ThemeProvider storageKey="test-theme">
        <ThemeConsumer />
      </ThemeProvider>
    );

    await userEvent.setup().click(screen.getByRole('button', { name: 'Set Dark' }));
    expect(localStorage.getItem('test-theme')).toBe('dark');
  });

  it('reads initial theme from localStorage', () => {
    localStorage.setItem('vite-ui-theme', 'dark');
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('uses custom storageKey', () => {
    localStorage.setItem('my-theme-key', 'light');
    render(
      <ThemeProvider storageKey="my-theme-key">
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
  });

  it('throws when useTheme is used outside provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<ThemeConsumer />)).toThrow('useTheme must be used within a ThemeProvider');
    consoleSpy.mockRestore();
  });

  it('does not add theme-transitioning on initial render', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(false);
  });

  it('adds and removes theme-transitioning on theme change', () => {
    vi.useFakeTimers();

    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    // Initial render should not have transitioning class
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(false);

    // Toggle theme using fireEvent (compatible with fake timers)
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Set Dark' }));
    });

    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    // After 600ms, the transitioning class should be removed
    act(() => {
      vi.advanceTimersByTime(600);
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(false);

    vi.useRealTimers();
  });

  it('resets the transition timeout on rapid theme toggles', () => {
    vi.useFakeTimers();

    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    // First toggle
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Set Dark' }));
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    // Advance partially (300ms of 600ms)
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    // Second toggle before first timeout completes — should restart the 600ms timer
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Set Light' }));
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    // Advance 300ms — first timeout would have fired but was cleared
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    // Advance remaining 300ms to complete the new timeout
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(false);

    vi.useRealTimers();
  });

  it('cleans up timeout on unmount to prevent memory leaks', () => {
    vi.useFakeTimers();

    const { unmount } = render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    // Trigger a theme change to start the timeout
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Set Dark' }));
    });
    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    // Unmount before the timeout fires
    unmount();

    // Advance past timeout — should not throw or cause errors
    act(() => {
      vi.advanceTimersByTime(600);
    });
    // Manually clean up (unmount doesn't remove the class from document)
    document.documentElement.classList.remove('theme-transitioning');

    vi.useRealTimers();
  });
});
