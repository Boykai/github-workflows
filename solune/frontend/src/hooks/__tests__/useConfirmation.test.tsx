/**
 * Tests for useConfirmation hook and ConfirmationDialogProvider.
 *
 * Covers: confirm resolves true/false, throws outside provider,
 * async onConfirm with loading/error, customizable options,
 * and queue management.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, renderHook, act, screen, fireEvent, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ConfirmationDialogProvider, useConfirmation } from '../useConfirmation';

function createWrapper() {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <ConfirmationDialogProvider>{children}</ConfirmationDialogProvider>;
  };
}

describe('useConfirmation', () => {
  it('throws when used outside ConfirmationDialogProvider', () => {
    // Suppress console.error for the expected error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => {
      renderHook(() => useConfirmation());
    }).toThrow('useConfirmation must be used within a ConfirmationDialogProvider');
    spy.mockRestore();
  });

  it('returns a confirm function', () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });
    expect(typeof result.current.confirm).toBe('function');
  });

  it('opens the dialog when confirm is called', async () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    act(() => {
      result.current.confirm({
        title: 'Test Title',
        description: 'Test Description',
      });
    });

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('resolves with true when confirm button is clicked', async () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    let resolved: boolean | undefined;
    act(() => {
      result.current
        .confirm({
          title: 'Confirm?',
          description: 'Are you sure?',
          confirmLabel: 'Yes',
        })
        .then((val) => {
          resolved = val;
        });
    });

    await waitFor(() => {
      expect(screen.getByText('Yes')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.click(screen.getByText('Yes'));
    });

    await waitFor(() => {
      expect(resolved).toBe(true);
    });
  });

  it('resolves with false when cancel button is clicked', async () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    let resolved: boolean | undefined;
    act(() => {
      result.current
        .confirm({
          title: 'Confirm?',
          description: 'Are you sure?',
        })
        .then((val) => {
          resolved = val;
        });
    });

    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.click(screen.getByText('Cancel'));
    });

    await waitFor(() => {
      expect(resolved).toBe(false);
    });
  });

  it('resolves with false when Escape key is pressed', async () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    let resolved: boolean | undefined;
    act(() => {
      result.current
        .confirm({
          title: 'Confirm?',
          description: 'Are you sure?',
        })
        .then((val) => {
          resolved = val;
        });
    });

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });

    await waitFor(() => {
      expect(resolved).toBe(false);
    });
  });

  it('passes customizable options through to the dialog', async () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    act(() => {
      result.current.confirm({
        title: 'Delete Agent',
        description: 'Remove agent "Reviewer"?',
        variant: 'danger',
        confirmLabel: 'Delete',
        cancelLabel: 'Keep',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Agent')).toBeInTheDocument();
    });
    expect(screen.getByText('Remove agent "Reviewer"?')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
    expect(screen.getByText('Keep')).toBeInTheDocument();
  });

  it('uses default variant and labels when not specified', async () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    act(() => {
      result.current.confirm({
        title: 'Action Required',
        description: 'Are you sure?',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Action Required')).toBeInTheDocument();
    });
    // Default confirmLabel is 'Confirm', default cancelLabel is 'Cancel'
    expect(screen.getByText('Confirm')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  // Async onConfirm
  it('shows loading state during async onConfirm', async () => {
    let resolveAsync: (() => void) | undefined;
    const asyncFn = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveAsync = resolve;
        })
    );

    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    act(() => {
      result.current.confirm({
        title: 'Async Test',
        description: 'Loading test',
        onConfirm: asyncFn,
        confirmLabel: 'Go',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Go')).toBeInTheDocument();
    });

    // Click confirm to trigger async handler
    await act(async () => {
      fireEvent.click(screen.getByText('Go'));
    });

    // Should show loading
    await waitFor(() => {
      expect(screen.getByText('Processing…')).toBeInTheDocument();
    });

    // Resolve the async function
    expect(resolveAsync).toBeDefined();
    await act(async () => {
      resolveAsync?.();
    });

    // Dialog should close
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    expect(asyncFn).toHaveBeenCalledOnce();
  });

  it('displays error message when async onConfirm fails', async () => {
    const asyncFn = vi.fn().mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    act(() => {
      result.current.confirm({
        title: 'Error Test',
        description: 'Error test',
        onConfirm: asyncFn,
        confirmLabel: 'Go',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Go')).toBeInTheDocument();
    });

    // Click confirm to trigger async handler that will fail
    await act(async () => {
      fireEvent.click(screen.getByText('Go'));
    });

    // Should show error
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    // Dialog should still be open (for retry)
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // Confirm button should be re-enabled for retry
    expect(screen.getByText('Go')).not.toBeDisabled();
  });

  // Queue management
  it('queues a second confirm while dialog is open', async () => {
    const { result } = renderHook(() => useConfirmation(), { wrapper: createWrapper() });

    let firstResolved: boolean | undefined;
    let secondResolved: boolean | undefined;

    act(() => {
      result.current
        .confirm({
          title: 'First Dialog',
          description: 'First',
          confirmLabel: 'OK First',
        })
        .then((val) => {
          firstResolved = val;
        });
    });

    await waitFor(() => {
      expect(screen.getByText('First Dialog')).toBeInTheDocument();
    });

    // Queue second dialog while first is open
    act(() => {
      result.current
        .confirm({
          title: 'Second Dialog',
          description: 'Second',
          confirmLabel: 'OK Second',
        })
        .then((val) => {
          secondResolved = val;
        });
    });

    // First dialog still showing
    expect(screen.getByText('First Dialog')).toBeInTheDocument();
    expect(screen.queryByText('Second Dialog')).not.toBeInTheDocument();

    // Close the first dialog
    act(() => {
      fireEvent.click(screen.getByText('OK First'));
    });

    await waitFor(() => {
      expect(firstResolved).toBe(true);
    });

    // Second dialog should now appear
    await waitFor(() => {
      expect(screen.getByText('Second Dialog')).toBeInTheDocument();
    });

    // Close second dialog
    act(() => {
      fireEvent.click(screen.getByText('OK Second'));
    });

    await waitFor(() => {
      expect(secondResolved).toBe(true);
    });
  });

  it('restores focus to the queued trigger after the final dialog closes', async () => {
    function FocusHarness() {
      const { confirm } = useConfirmation();

      return (
        <div>
          <button
            type="button"
            onClick={() => {
              void confirm({
                title: 'First Dialog',
                description: 'First',
                confirmLabel: 'OK First',
              });
            }}
          >
            Open First
          </button>
          <button
            type="button"
            onClick={() => {
              void confirm({
                title: 'Second Dialog',
                description: 'Second',
                confirmLabel: 'OK Second',
              });
            }}
          >
            Open Second
          </button>
        </div>
      );
    }

    render(<FocusHarness />, { wrapper: createWrapper() });

    const firstTrigger = screen.getByText('Open First');
    const secondTrigger = screen.getByText('Open Second');

    act(() => {
      firstTrigger.focus();
      fireEvent.click(firstTrigger);
    });

    await waitFor(() => {
      expect(screen.getByText('First Dialog')).toBeInTheDocument();
    });

    act(() => {
      secondTrigger.focus();
      fireEvent.click(secondTrigger);
    });

    act(() => {
      fireEvent.click(screen.getByText('OK First'));
    });

    await waitFor(() => {
      expect(screen.getByText('Second Dialog')).toBeInTheDocument();
    });

    act(() => {
      fireEvent.click(screen.getByText('Cancel'));
    });

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    await waitFor(() => {
      expect(document.activeElement).toBe(secondTrigger);
    });
  });
});
