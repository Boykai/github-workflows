/**
 * useConfirmation — imperative confirmation dialog via React Context.
 *
 * Provides a Promise-based `confirm()` API that opens a single shared
 * ConfirmationDialog instance at the app root.  Queues concurrent requests
 * to enforce at most one visible dialog at a time.  Captures and restores
 * focus to the triggering element after close.
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from 'react';
import {
  ConfirmationDialog,
  type ConfirmationVariant,
} from '@/components/ui/confirmation-dialog';

/* ------------------------------------------------------------------ */
/*  Public types                                                       */
/* ------------------------------------------------------------------ */

export interface ConfirmationOptions {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmationVariant;
}

interface ConfirmationContextValue {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}

/* ------------------------------------------------------------------ */
/*  Internal types                                                     */
/* ------------------------------------------------------------------ */

interface QueueItem {
  options: ConfirmationOptions;
  resolve: (value: boolean) => void;
}

/* ------------------------------------------------------------------ */
/*  Context                                                            */
/* ------------------------------------------------------------------ */

const ConfirmationContext = createContext<ConfirmationContextValue | null>(null);

/* ------------------------------------------------------------------ */
/*  Provider                                                           */
/* ------------------------------------------------------------------ */

export function ConfirmationProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentOptions, setCurrentOptions] = useState<ConfirmationOptions | null>(null);
  const resolverRef = useRef<((value: boolean) => void) | null>(null);
  const queueRef = useRef<QueueItem[]>([]);
  const triggerElementRef = useRef<Element | null>(null);

  const openDialog = useCallback((options: ConfirmationOptions, resolve: (value: boolean) => void) => {
    triggerElementRef.current = document.activeElement;
    resolverRef.current = resolve;
    setCurrentOptions(options);
    setIsOpen(true);
  }, []);

  const closeDialog = useCallback((result: boolean) => {
    resolverRef.current?.(result);
    resolverRef.current = null;
    setIsOpen(false);
    setCurrentOptions(null);

    // Restore focus to triggering element
    const triggerEl = triggerElementRef.current;
    if (triggerEl && triggerEl instanceof HTMLElement) {
      requestAnimationFrame(() => triggerEl.focus());
    }
    triggerElementRef.current = null;

    // Dequeue next request if any
    const next = queueRef.current.shift();
    if (next) {
      // Small delay to let the previous dialog unmount
      requestAnimationFrame(() => openDialog(next.options, next.resolve));
    }
  }, [openDialog]);

  const confirm = useCallback(
    (options: ConfirmationOptions): Promise<boolean> => {
      return new Promise<boolean>((resolve) => {
        if (isOpen) {
          queueRef.current.push({ options, resolve });
        } else {
          openDialog(options, resolve);
        }
      });
    },
    [isOpen, openDialog],
  );

  return (
    <ConfirmationContext.Provider value={{ confirm }}>
      {children}
      <ConfirmationDialog
        isOpen={isOpen}
        title={currentOptions?.title ?? ''}
        description={currentOptions?.description ?? ''}
        confirmLabel={currentOptions?.confirmLabel ?? 'Confirm'}
        cancelLabel={currentOptions?.cancelLabel ?? 'Cancel'}
        variant={currentOptions?.variant ?? 'info'}
        onConfirm={() => closeDialog(true)}
        onCancel={() => closeDialog(false)}
      />
    </ConfirmationContext.Provider>
  );
}

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

export function useConfirmation(): ConfirmationContextValue {
  const ctx = useContext(ConfirmationContext);
  if (!ctx) {
    throw new Error('useConfirmation must be used within a ConfirmationProvider');
  }
  return ctx;
}
