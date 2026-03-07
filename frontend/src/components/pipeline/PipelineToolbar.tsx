/**
 * PipelineToolbar — persistent action bar with Create/Save/Delete/Discard.
 * Button states follow the toolbar state matrix from data-model.md.
 */

import { Plus, Save, Trash2, RotateCcw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { PipelineBoardState } from '@/types';

interface PipelineToolbarProps {
  boardState: PipelineBoardState;
  isDirty: boolean;
  isSaving: boolean;
  pipelineName?: string;
  onNewPipeline: () => void;
  onSave: () => void;
  onDelete: () => void;
  onDiscard: () => void;
}

export function PipelineToolbar({
  boardState,
  isDirty,
  isSaving,
  pipelineName,
  onNewPipeline,
  onSave,
  onDelete,
  onDiscard,
}: PipelineToolbarProps) {
  // Toolbar state matrix from data-model.md
  const hasName = !!pipelineName?.trim();
  const isNewEnabled = boardState === 'empty' || (boardState === 'editing');
  const isSaveEnabled =
    hasName && ((boardState === 'creating' && isDirty) || (boardState === 'editing' && isDirty));
  const isDiscardEnabled =
    (boardState === 'creating' && isDirty) || (boardState === 'editing' && isDirty);
  const isDeleteEnabled = boardState === 'editing';

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={onNewPipeline}
        disabled={!isNewEnabled}
      >
        <Plus className="mr-1.5 h-3.5 w-3.5" />
        New Pipeline
      </Button>

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
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={onDiscard}
        disabled={!isDiscardEnabled}
      >
        <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
        Discard
      </Button>

      <Button
        variant="destructive"
        size="sm"
        onClick={onDelete}
        disabled={!isDeleteEnabled}
      >
        <Trash2 className="mr-1.5 h-3.5 w-3.5" />
        Delete
      </Button>
    </div>
  );
}
