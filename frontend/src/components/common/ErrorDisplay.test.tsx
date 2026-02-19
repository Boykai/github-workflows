/**
 * Unit tests for ErrorDisplay components
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { ErrorToast, ErrorBanner } from './ErrorDisplay';

describe('ErrorToast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders null when error is null', () => {
    const { container } = render(<ErrorToast error={null} onDismiss={vi.fn()} />);
    expect(container.innerHTML).toBe('');
  });

  it('shows user-friendly message for auth errors', () => {
    const error = new Error('401 Unauthorized');
    render(<ErrorToast error={error} onDismiss={vi.fn()} />);
    expect(screen.getByText('Your session has expired. Please log in again.')).toBeDefined();
  });

  it('dismiss button calls onDismiss after animation delay', () => {
    const onDismiss = vi.fn();
    const error = new Error('Some error');
    render(<ErrorToast error={error} onDismiss={onDismiss} />);

    fireEvent.click(screen.getByLabelText('Dismiss error'));

    // onDismiss is called after 300ms animation delay
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(onDismiss).toHaveBeenCalled();
  });

  it('auto-dismisses after 5 seconds', () => {
    const onDismiss = vi.fn();
    const error = new Error('Timeout error');
    render(<ErrorToast error={error} onDismiss={onDismiss} />);

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(onDismiss).toHaveBeenCalled();
  });

  it('has role alert for accessibility', () => {
    const error = new Error('Test error');
    render(<ErrorToast error={error} onDismiss={vi.fn()} />);
    expect(screen.getByRole('alert')).toBeDefined();
  });
});

describe('ErrorBanner', () => {
  it('renders null when error is null', () => {
    const { container } = render(<ErrorBanner error={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('shows message and retry button', () => {
    const retry = vi.fn();
    const error = new Error('Server error 500');
    render(<ErrorBanner error={error} retry={retry} />);

    expect(screen.getByText('Something went wrong')).toBeDefined();
    expect(screen.getByText('Server error. Please try again later.')).toBeDefined();
    expect(screen.getByText('Try Again')).toBeDefined();
  });

  it('calls retry when retry button clicked', () => {
    const retry = vi.fn();
    render(<ErrorBanner error={new Error('error')} retry={retry} />);

    fireEvent.click(screen.getByText('Try Again'));
    expect(retry).toHaveBeenCalledOnce();
  });

  it('does not show retry button when retry prop is not provided', () => {
    render(<ErrorBanner error={new Error('error')} />);
    expect(screen.queryByText('Try Again')).toBeNull();
  });
});

describe('getUserFriendlyMessage mapping', () => {
  const testCases = [
    { input: '401 error', expected: 'Your session has expired. Please log in again.' },
    { input: 'authentication failed', expected: 'Your session has expired. Please log in again.' },
    { input: '403 forbidden', expected: "You don't have permission to perform this action." },
    { input: 'access denied', expected: "You don't have permission to perform this action." },
    { input: '404 missing', expected: 'The requested resource was not found.' },
    { input: 'not found', expected: 'The requested resource was not found.' },
    { input: '429 too many', expected: 'Too many requests. Please wait a moment and try again.' },
    { input: 'rate limit exceeded', expected: 'Too many requests. Please wait a moment and try again.' },
    { input: '502 bad gateway', expected: 'Unable to connect to GitHub. Please check your connection and try again.' },
    { input: 'github api error', expected: 'Unable to connect to GitHub. Please check your connection and try again.' },
    { input: 'network error', expected: 'Network error. Please check your internet connection.' },
    { input: 'fetch failed', expected: 'Network error. Please check your internet connection.' },
    { input: '422 unprocessable', expected: 'Invalid input. Please check your data and try again.' },
    { input: 'validation error', expected: 'Invalid input. Please check your data and try again.' },
    { input: '500 internal', expected: 'Server error. Please try again later.' },
    { input: 'some unknown error', expected: 'some unknown error' },
  ];

  testCases.forEach(({ input, expected }) => {
    it(`maps "${input}" to friendly message`, () => {
      // ErrorBanner renders the friendly message so we use it to test the mapping
      render(<ErrorBanner error={new Error(input)} />);
      expect(screen.getByText(expected)).toBeDefined();
    });
  });
});


