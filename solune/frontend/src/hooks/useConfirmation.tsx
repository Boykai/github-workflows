/**
 * useConfirmation — imperative confirmation hook with context-based dialog management.
 *
 * Provides `confirm(options)` returning `Promise<boolean>` via React Context.
 * Renders a single ConfirmationDialog at the provider level with queue management,
 * focus capture/restoration, and async onConfirm support.
 */

import { createContext, useContext, useState, useCallback, useRef } from 'react';
import type { ReactNode } from 'react';
import { ConfirmationDialog, type ConfirmationVariant } from '@/components/ui/confirmation-dialog';

export interface ConfirmationOptions {
  title: string;
  description: string;
  variant?: ConfirmationVariant;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => Promise<void>;
}

interface UseConfirmationReturn {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}

interface DialogState {
  isOpen: boolean;
  options: Required<Pick<ConfirmationOptions, 'title' | 'description'>> & {
    variant: ConfirmationVariant;
    confirmLabel: string;
    cancelLabel: string;
    onConfirm?: () => Promise<void>;
  };
  isLoading: boolean;
  error: string | null;
}

interface QueuedRequest {
  options: DialogState['options'];
  resolve: (value: boolean) => void;
  previousFocus: HTMLElement | null;
}

const DEFAULT_STATE: DialogState = {
  isOpen: false,
  options: {
    title: '',
    description: '',
    variant: 'danger',
    confirmLabel: 'Confirm',
    cancelLabel: 'Cancel',
  },
  isLoading: false,
  error: null,
};

const ConfirmationContext = createContext<UseConfirmationReturn | null>(null);

export function ConfirmationDialogProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DialogState>(DEFAULT_STATE);
  const resolveRef = useRef<((value: boolean) => void) | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const queueRef = useRef<QueuedRequest[]>([]);

  const openDialog = useCallback((request: QueuedRequest) => {
    previousFocusRef.current = request.previousFocus;
    resolveRef.current = request.resolve;
    setState({
      isOpen: true,
      options: request.options,
      isLoading: false,
      error: null,
    });
  }, []);

  const processQueue = useCallback(() => {
    if (queueRef.current.length === 0) return;
    const next = queueRef.current.shift()!;
    openDialog(next);
  }, [openDialog]);

  const closeDialog = useCallback(
    (result: boolean) => {
      const resolve = resolveRef.current;
      const focusToRestore = previousFocusRef.current;
      resolveRef.current = null;
      previousFocusRef.current = null;
      setState(DEFAULT_STATE);

      requestAnimationFrame(() => {
        if (focusToRestore?.isConnected) {
          focusToRestore.focus();
        }

        processQueue();
      });

      resolve?.(result);
    },
    [processQueue]
  );

  const confirm = useCallback(
    (options: ConfirmationOptions): Promise<boolean> => {
      const fullOptions: DialogState['options'] = {
        title: options.title,
        description: options.description,
        variant: options.variant ?? 'danger',
        confirmLabel: options.confirmLabel ?? 'Confirm',
        cancelLabel: options.cancelLabel ?? 'Cancel',
        onConfirm: options.onConfirm,
      };

      return new Promise<boolean>((resolve) => {
        const previousFocus =
          document.activeElement instanceof HTMLElement ? document.activeElement : null;

        // If a dialog is already open, queue this request
        if (state.isOpen || resolveRef.current) {
          queueRef.current.push({
            options: fullOptions,
            resolve,
            previousFocus,
          });
          return;
        }

        openDialog({
          options: fullOptions,
          resolve,
          previousFocus,
        });
      });
    },
    [openDialog, state.isOpen]
  );

  const handleConfirm = useCallback(async () => {
    if (state.isLoading) return; // Double-click prevention

    if (state.options.onConfirm) {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));
      try {
        await state.options.onConfirm();
        closeDialog(true);
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : 'An unexpected error occurred',
        }));
      }
    } else {
      closeDialog(true);
    }
  }, [state.isLoading, state.options, closeDialog]);

  const handleCancel = useCallback(() => {
    if (state.isLoading) return;
    closeDialog(false);
  }, [state.isLoading, closeDialog]);

  return (
    <ConfirmationContext.Provider value={{ confirm }}>
      {children}
      <ConfirmationDialog
        isOpen={state.isOpen}
        title={state.options.title}
        description={state.options.description}
        variant={state.options.variant}
        confirmLabel={state.options.confirmLabel}
        cancelLabel={state.options.cancelLabel}
        isLoading={state.isLoading}
        error={state.error}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </ConfirmationContext.Provider>
  );
}

export function useConfirmation(): UseConfirmationReturn {
  const context = useContext(ConfirmationContext);
  if (!context) {
    throw new Error('useConfirmation must be used within a ConfirmationDialogProvider');
  }
  return context;
}
