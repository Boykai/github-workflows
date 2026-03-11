/**
 * UnsavedChangesDialog — confirmation dialog for unsaved changes.
 * Shows Save, Discard, and Cancel options.
 */

import { useEffect, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface UnsavedChangesDialogProps {
  isOpen: boolean;
  onSave: () => void;
  onDiscard: () => void;
  onCancel: () => void;
  actionDescription?: string;
}

export function UnsavedChangesDialog({
  isOpen,
  onSave,
  onDiscard,
  onCancel,
  actionDescription,
}: UnsavedChangesDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);

  // Focus trap and Escape key handling
  useEffect(() => {
    if (!isOpen) return;

    // Focus cancel button when dialog opens
    requestAnimationFrame(() => {
      cancelBtnRef.current?.focus();
    });

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
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
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onCancel}
        role="presentation"
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="unsaved-changes-title"
        aria-describedby="unsaved-changes-description"
        className="celestial-fade-in relative z-10 mx-4 w-full max-w-md rounded-2xl border border-border/80 bg-card p-6 shadow-xl"
      >
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-amber-100/80 p-2 dark:bg-amber-950/50">
            <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="flex-1">
            <h3 id="unsaved-changes-title" className="text-base font-semibold text-foreground">Unsaved Changes</h3>
            <p id="unsaved-changes-description" className="mt-1 text-sm text-muted-foreground">
              You have unsaved changes
              {actionDescription ? `. ${actionDescription}` : ''}. What would you like to do?
            </p>
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <Button ref={cancelBtnRef} variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="outline" size="sm" onClick={onDiscard}>
            Discard
          </Button>
          <Button variant="default" size="sm" onClick={onSave}>
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}
