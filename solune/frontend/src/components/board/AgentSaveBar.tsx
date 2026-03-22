import { TriangleAlert } from '@/lib/icons';

/**
 * AgentSaveBar component - floating bar with Save/Discard buttons.
 * Only visible when there are unsaved changes (isDirty).
 */

interface AgentSaveBarProps {
  onSave: () => void;
  onDiscard: () => void;
  isSaving: boolean;
  error: string | null;
}

export function AgentSaveBar({ onSave, onDiscard, isSaving, error }: AgentSaveBarProps) {
  return (
    <div
      className="celestial-panel absolute bottom-4 left-1/2 z-50 flex -translate-x-1/2 items-center gap-4 rounded-full border border-border px-4 py-2 shadow-lg animate-in slide-in-from-bottom-4 fade-in duration-200"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-foreground">You have unsaved changes</span>

        {error && (
          <span className="text-xs text-destructive bg-destructive/10 px-2 py-1 rounded-md flex items-center gap-1">
            <TriangleAlert className="h-3.5 w-3.5" />
            {error}
          </span>
        )}

        <div className="flex items-center gap-2">
          <button
            className="celestial-focus solar-action rounded-full px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={onDiscard}
            disabled={isSaving}
            type="button"
            aria-label="Discard unsaved changes"
          >
            Discard
          </button>
          <button
            className="celestial-focus px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={onSave}
            disabled={isSaving}
            type="button"
            aria-label={isSaving ? 'Saving changes' : 'Save changes'}
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
