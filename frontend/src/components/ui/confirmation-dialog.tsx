/**
 * ConfirmationDialog — reusable modal dialog for confirming critical actions.
 *
 * Supports three severity variants (danger, warning, info) with matching icons
 * and button styling. Renders via portal at document body level.
 * Meets WCAG 2.1 AA: role="alertdialog", aria-modal, focus trap, Escape to cancel.
 */

import { useEffect, useRef, useId } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';

export type ConfirmationVariant = 'danger' | 'warning' | 'info';

export interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel: string;
  variant: ConfirmationVariant;
  onConfirm: () => void;
  onCancel: () => void;
}

const VARIANT_CONFIG: Record<
  ConfirmationVariant,
  {
    Icon: typeof AlertTriangle;
    iconBg: string;
    iconColor: string;
    confirmButtonVariant: 'destructive' | 'default';
  }
> = {
  danger: {
    Icon: AlertTriangle,
    iconBg: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600 dark:text-red-400',
    confirmButtonVariant: 'destructive',
  },
  warning: {
    Icon: AlertTriangle,
    iconBg: 'bg-amber-100 dark:bg-amber-900/30',
    iconColor: 'text-amber-600 dark:text-amber-400',
    confirmButtonVariant: 'default',
  },
  info: {
    Icon: Info,
    iconBg: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600 dark:text-blue-400',
    confirmButtonVariant: 'default',
  },
};

export function ConfirmationDialog({
  isOpen,
  title,
  description,
  confirmLabel,
  cancelLabel,
  variant,
  onConfirm,
  onCancel,
}: ConfirmationDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const uniqueId = useId();
  const titleId = `${uniqueId}-title`;
  const descId = `${uniqueId}-description`;

  // Focus trap + Escape handler
  useEffect(() => {
    if (!isOpen || !dialogRef.current) return;

    const dialog = dialogRef.current;
    const focusableElements = dialog.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    // Focus the first button (Cancel) on open
    firstFocusable?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel();
        return;
      }

      if (e.key === 'Tab') {
        if (focusableElements.length === 0) {
          e.preventDefault();
          return;
        }
        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            e.preventDefault();
            lastFocusable.focus();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            e.preventDefault();
            firstFocusable.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const { Icon, iconBg, iconColor, confirmButtonVariant } = VARIANT_CONFIG[variant];

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onCancel();
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="none"
      onClick={handleBackdropClick}
    >
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="relative w-full max-w-md mx-4 rounded-[1.4rem] border border-border bg-background p-6 shadow-xl"
      >
        <div className="flex flex-col items-center gap-4 text-center">
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-full ${iconBg}`}
          >
            <Icon className={`h-6 w-6 ${iconColor}`} />
          </div>

          <h2
            id={titleId}
            className="text-lg font-semibold text-foreground"
          >
            {title}
          </h2>

          <p
            id={descId}
            className="max-h-40 overflow-y-auto text-sm text-muted-foreground"
          >
            {description}
          </p>

          <div className="flex gap-3 pt-2">
            <Button variant="outline" size="sm" onClick={onCancel}>
              {cancelLabel}
            </Button>
            <Button variant={confirmButtonVariant} size="sm" onClick={onConfirm}>
              {confirmLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
