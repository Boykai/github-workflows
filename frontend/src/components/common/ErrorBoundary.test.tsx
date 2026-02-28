/**
 * Unit tests for ErrorBoundary component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

// Suppress React error boundary console.error noise in test output.
// The spy is stored so it can be restored in afterEach to prevent leaking
// the mock into other test files.
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  consoleErrorSpy.mockRestore();
});

function ThrowingComponent({ error }: { error: Error }) {
  throw error;
}

function SafeComponent() {
  return <div>Safe content</div>;
}

describe('ErrorBoundary', () => {
  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <SafeComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Safe content')).toBeDefined();
  });

  it('should render default fallback when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error('Test crash')} />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('alert')).toBeDefined();
    expect(screen.getByText('Something went wrong')).toBeDefined();
    expect(screen.getByText('Test crash')).toBeDefined();
  });

  it('should render custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom error UI</div>}>
        <ThrowingComponent error={new Error('Boom')} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Custom error UI')).toBeDefined();
  });

  it('should reset state when Try again button is clicked', () => {
    const onReset = vi.fn();
    let shouldThrow = true;

    function ConditionalThrow() {
      if (shouldThrow) {
        throw new Error('Will recover');
      }
      return <div>Recovered content</div>;
    }

    render(
      <ErrorBoundary onReset={onReset}>
        <ConditionalThrow />
      </ErrorBoundary>,
    );

    // Should show error fallback
    expect(screen.getByText('Something went wrong')).toBeDefined();

    // Fix the component before resetting
    shouldThrow = false;

    // Click "Try again"
    fireEvent.click(screen.getByText('Try again'));

    expect(onReset).toHaveBeenCalledOnce();
  });

  it('should display the error message in the default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error('Detailed error message')} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Detailed error message')).toBeDefined();
  });
});
