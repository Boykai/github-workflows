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
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-50 bg-card border border-border rounded-full shadow-lg px-4 py-2 flex items-center gap-4 animate-in slide-in-from-bottom-4 fade-in duration-200">
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-foreground">You have unsaved changes</span>

        {error && (
          <span className="text-xs text-destructive bg-destructive/10 px-2 py-1 rounded-md flex items-center gap-1">
            ⚠ {error}
          </span>
        )}

        <div className="flex items-center gap-2">
          <button
            className="px-3 py-1.5 text-sm font-medium rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={onDiscard}
            disabled={isSaving}
            type="button"
          >
            Discard
          </button>
          <button
            className="px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={onSave}
            disabled={isSaving}
            type="button"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
