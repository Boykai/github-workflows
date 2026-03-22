/**
 * ConfirmationDialog — reusable, accessible confirmation dialog for critical actions.
 *
 * Supports danger/warning/info variants, async loading states with spinner,
 * inline error display, focus trapping, and ARIA attributes for WCAG 2.1 AA.
 */

import { useEffect, useRef } from 'react';
import { AlertTriangle, Info, Loader2 } from '@/lib/icons';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type ConfirmationVariant = 'danger' | 'warning' | 'info';

export interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  variant: ConfirmationVariant;
  confirmLabel: string;
  cancelLabel: string;
  isLoading: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

const VARIANT_CONFIG: Record<
  ConfirmationVariant,
  {
    Icon: typeof AlertTriangle | typeof Info;
    iconClass: string;
    iconBgClass: string;
    confirmBtnClass: string;
  }
> = {
  danger: {
    Icon: AlertTriangle,
    iconClass: 'text-red-500',
    iconBgClass: 'bg-red-100/80 dark:bg-red-950/50',
    confirmBtnClass:
      'bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed',
  },
  warning: {
    Icon: AlertTriangle,
    iconClass: 'text-amber-500',
    iconBgClass: 'bg-amber-100/80 dark:bg-amber-950/50',
    confirmBtnClass:
      'bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-50 disabled:cursor-not-allowed',
  },
  info: {
    Icon: Info,
    iconClass: 'text-blue-500',
    iconBgClass: 'bg-blue-100/80 dark:bg-blue-950/50',
    confirmBtnClass:
      'bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed',
  },
};

export function ConfirmationDialog({
  isOpen,
  title,
  description,
  variant,
  confirmLabel,
  cancelLabel,
  isLoading,
  error,
  onConfirm,
  onCancel,
}: ConfirmationDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);

  // Focus the cancel button (safe default) when dialog opens
  useEffect(() => {
    if (isOpen) {
      // Small delay to ensure DOM is rendered before focusing
      requestAnimationFrame(() => {
        cancelBtnRef.current?.focus();
      });
    }
  }, [isOpen]);

  // Focus trapping and Escape key handling
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        e.preventDefault();
        onCancel();
        return;
      }

      if (e.key === 'Tab' && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [tabindex]:not([tabindex="-1"]), a[href], input, select, textarea'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onCancel]);

  if (!isOpen) return null;

  const { Icon, iconClass, iconBgClass, confirmBtnClass } = VARIANT_CONFIG[variant];

  const handleBackdropClick = () => {
    if (!isLoading) {
      onCancel();
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={isLoading ? undefined : handleBackdropClick}
        role="presentation"
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmation-dialog-title"
        aria-describedby="confirmation-dialog-description"
        className="relative z-10 mx-4 w-full max-w-md rounded-2xl border border-border/80 bg-card p-6 shadow-xl"
      >
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className={cn('shrink-0 rounded-full p-2', iconBgClass)}>
            <Icon className={cn('h-5 w-5', iconClass)} />
          </div>
          <h3
            id="confirmation-dialog-title"
            className="text-base font-semibold text-foreground pt-1.5"
          >
            {title}
          </h3>
        </div>

        {/* Description (scrollable) */}
        <div
          id="confirmation-dialog-description"
          className="mt-3 max-h-[60vh] overflow-y-auto text-sm leading-relaxed text-muted-foreground"
        >
          {description}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Buttons */}
        <div className="mt-5 flex justify-end gap-2">
          <Button
            ref={cancelBtnRef}
            type="button"
            variant="ghost"
            size="sm"
            className="rounded-lg text-foreground"
            onClick={onCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            size="sm"
            className={cn('gap-2 rounded-lg', confirmBtnClass)}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {isLoading ? 'Processing…' : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
