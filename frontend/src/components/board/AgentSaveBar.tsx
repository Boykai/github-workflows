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
    <div className="agent-save-bar">
      <div className="agent-save-bar-content">
        <span className="agent-save-bar-label">You have unsaved changes</span>

        {error && (
          <span className="agent-save-bar-error">
            ⚠ {error}
          </span>
        )}

        <div className="agent-save-bar-actions">
          <button
            className="agent-save-bar-btn agent-save-bar-btn--discard"
            onClick={onDiscard}
            disabled={isSaving}
            type="button"
          >
            Discard
          </button>
          <button
            className="agent-save-bar-btn agent-save-bar-btn--save"
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
