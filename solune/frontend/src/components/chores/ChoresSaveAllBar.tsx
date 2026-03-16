/**
 * ChoresSaveAllBar — unsaved changes banner with discard/save-all actions.
 *
 * Extracted from ChoresPanel for single-responsibility.
 */

import { Button } from '@/components/ui/button';

interface ChoresSaveAllBarProps {
  isVisible: boolean;
  isSaving: boolean;
  onDiscardAll: () => void;
  onSaveAll: () => void;
}

export function ChoresSaveAllBar({
  isVisible,
  isSaving,
  onDiscardAll,
  onSaveAll,
}: ChoresSaveAllBarProps) {
  if (!isVisible) return null;

  return (
    <div
      className="flex items-center justify-between gap-4 rounded-[1.2rem] border border-yellow-500/30 bg-yellow-50 px-4 py-3 dark:bg-yellow-900/20"
      role="status"
      aria-live="polite"
    >
      <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
        You have unsaved changes
      </p>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={onDiscardAll} disabled={isSaving}>
          Discard All
        </Button>
        <Button size="sm" onClick={onSaveAll} disabled={isSaving}>
          {isSaving ? 'Saving…' : 'Save All'}
        </Button>
      </div>
    </div>
  );
}
