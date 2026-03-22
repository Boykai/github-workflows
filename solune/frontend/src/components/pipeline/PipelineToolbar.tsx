/**
 * PipelineToolbar — persistent action bar with Create/Save/Delete/Discard.
 * Save is always enabled during creation/editing. Presets show "Save as Copy".
 */

import { useEffect, useState } from 'react';
import { Save, Copy, Trash2, RotateCcw, Loader2 } from '@/lib/icons';
import { Button } from '@/components/ui/button';
import type { PipelineBoardState, PipelineValidationErrors } from '@/types';
import { useScrollLock } from '@/hooks/useScrollLock';

interface PipelineToolbarProps {
  boardState: PipelineBoardState;
  isDirty: boolean;
  isSaving: boolean;
  isPreset: boolean;
  pipelineName?: string;
  validationErrors: PipelineValidationErrors;
  onSave: () => void;
  onSaveAsCopy: (newName: string) => void;
  onDelete: () => void;
  onDiscard: () => void;
}

export function PipelineToolbar({
  boardState,
  isDirty,
  isSaving,
  isPreset,
  pipelineName,
  validationErrors,
  onSave,
  onSaveAsCopy,
  onDelete,
  onDiscard,
}: PipelineToolbarProps) {
  const [showCopyDialog, setShowCopyDialog] = useState(false);
  const [copyName, setCopyName] = useState('');

  // Save is always enabled when board is not empty (FR-007)
  const isSaveEnabled = boardState === 'creating' || (boardState === 'editing' && !isPreset);
  const isDiscardEnabled =
    (boardState === 'creating' && isDirty) || (boardState === 'editing' && isDirty);
  const isDeleteEnabled = boardState === 'editing' && !isPreset;
  const errorCount = Object.keys(validationErrors).length;

  const handleSaveAsCopy = () => {
    const name = copyName.trim();
    if (name) {
      onSaveAsCopy(name);
      setShowCopyDialog(false);
      setCopyName('');
    }
  };

  useScrollLock(showCopyDialog);

  useEffect(() => {
    if (!showCopyDialog) return undefined;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowCopyDialog(false);
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => {
      window.removeEventListener('keydown', handleEscape);
    };
  }, [showCopyDialog]);

  return (
    <div className="flex items-center gap-2 rounded-[1rem] border border-border/65 bg-background/35 p-1.5 dark:border-border/80 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.94)_0%,hsl(var(--panel)/0.86)_100%)]">
      <div className="flex items-center gap-2">
        {isPreset && boardState === 'editing' ? (
          <>
            <Button
              variant="default"
              size="sm"
              onClick={() => {
                setCopyName(`${pipelineName ?? ''} (Copy)`);
                setShowCopyDialog(true);
              }}
              disabled={isSaving}
            >
              <Copy className="mr-1.5 h-3.5 w-3.5" />
              Save as Copy
            </Button>

            {showCopyDialog && (
              <div
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
                role="presentation"
                onClick={(e) => {
                  if (e.target === e.currentTarget) {
                    setShowCopyDialog(false);
                  }
                }}
              >
                <div
                  className="celestial-fade-in w-80 rounded-lg border border-border bg-card p-4 shadow-lg dark:border-border/80 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.97)_0%,hsl(var(--panel)/0.92)_100%)]"
                  role="dialog"
                  aria-modal="true"
                  aria-labelledby="copy-dialog-title"
                >
                  <h3 id="copy-dialog-title" className="text-sm font-semibold mb-2">
                    Save as Copy
                  </h3>
                  <input
                    type="text"
                    value={copyName}
                    onChange={(e) => setCopyName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveAsCopy();
                    }}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm dark:border-border/80 dark:bg-background/80"
                    placeholder="New pipeline name"
                    maxLength={100}
                  />
                  <div className="flex justify-end gap-2 mt-3">
                    <Button variant="ghost" size="sm" onClick={() => setShowCopyDialog(false)}>
                      Cancel
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleSaveAsCopy}
                      disabled={!copyName.trim()}
                    >
                      Save
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <Button
            variant="default"
            size="sm"
            onClick={onSave}
            disabled={!isSaveEnabled || isSaving}
          >
            {isSaving ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="mr-1.5 h-3.5 w-3.5" />
            )}
            Save
            {errorCount > 0 && (
              <span className="ml-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                {errorCount}
              </span>
            )}
          </Button>
        )}

        <Button variant="ghost" size="sm" onClick={onDiscard} disabled={!isDiscardEnabled}>
          <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
          Discard
        </Button>

        <Button variant="destructive" size="sm" onClick={onDelete} disabled={!isDeleteEnabled}>
          <Trash2 className="mr-1.5 h-3.5 w-3.5" />
          Delete
        </Button>
      </div>

    </div>
  );
}
