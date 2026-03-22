/**
 * UnsavedChangesDialog — confirmation dialog for unsaved changes.
 * Shows Save, Discard, and Cancel options.
 */

import { AlertTriangle } from '@/lib/icons';
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
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onCancel}
        onKeyDown={(e) => {
          if (e.key === 'Escape') onCancel();
        }}
        role="button"
        tabIndex={0}
        aria-label="Close dialog"
      />

      {/* Dialog */}
      <div className="celestial-fade-in relative z-10 mx-4 w-full max-w-md rounded-2xl border border-border/80 bg-card p-6 shadow-xl">
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-amber-100/80 p-2 dark:bg-amber-950/50">
            <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-semibold text-foreground">Unsaved Changes</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              You have unsaved changes
              {actionDescription ? `. ${actionDescription}` : ''}. What would you like to do?
            </p>
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={onCancel}>
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
