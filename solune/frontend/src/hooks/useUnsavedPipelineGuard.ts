/**
 * useUnsavedPipelineGuard — Manages unsaved changes dialog state and
 * guards for the pipeline editor. Extracted from AgentsPipelinePage.
 */

import { useState, useCallback } from 'react';
import type { ConfirmationOptions } from '@/hooks/useConfirmation';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import { useUndoableDelete } from '@/hooks/useUndoableDelete';
import { pipelineKeys } from '@/hooks/usePipelineConfig';

interface PipelineConfigActions {
  isDirty: boolean;
  editingPipelineId: string | null;
  pipeline: { name: string } | null;
  loadPipeline: (pipelineId: string) => Promise<unknown>;
  duplicatePipeline: (pipelineId: string) => Promise<unknown>;
  newPipeline: (stageNames: string[]) => void;
  deletePipeline: () => Promise<unknown>;
  savePipeline: () => Promise<unknown>;
  discardChanges: () => void;
}

interface UseUnsavedPipelineGuardOptions {
  pipelineConfig: PipelineConfigActions;
  projectId: string | null;
  confirm: (opts: ConfirmationOptions) => Promise<boolean>;
  focusPipelineEditor: () => void;
  columns: { status: { name: string } }[];
}

export function useUnsavedPipelineGuard({
  pipelineConfig,
  projectId,
  confirm,
  focusPipelineEditor,
  columns,
}: UseUnsavedPipelineGuardOptions) {
  const [unsavedDialog, setUnsavedDialog] = useState<{
    isOpen: boolean;
    pendingAction: (() => void) | null;
    description: string;
  }>({ isOpen: false, pendingAction: null, description: '' });

  // Reuse the generic unsaved-changes guard for beforeunload + SPA navigation blocking
  const { blocker, isBlocked } = useUnsavedChanges({ isDirty: pipelineConfig.isDirty });

  const { undoableDelete } = useUndoableDelete({
    queryKeys: projectId ? [pipelineKeys.list(projectId)] : [],
  });

  const handleWorkflowSelect = useCallback(
    (pipelineId: string) => {
      if (pipelineConfig.isDirty) {
        setUnsavedDialog({
          isOpen: true,
          pendingAction: async () => {
            await pipelineConfig.loadPipeline(pipelineId);
            focusPipelineEditor();
          },
          description: 'Loading a different workflow will discard your changes',
        });
      } else {
        pipelineConfig.loadPipeline(pipelineId).then(() => {
          focusPipelineEditor();
        });
      }
    },
    [focusPipelineEditor, pipelineConfig],
  );

  const handleWorkflowCopy = useCallback(
    (pipelineId: string) => {
      if (pipelineConfig.isDirty) {
        setUnsavedDialog({
          isOpen: true,
          pendingAction: async () => {
            await pipelineConfig.duplicatePipeline(pipelineId);
            focusPipelineEditor();
          },
          description: 'Copying a saved workflow will discard your changes',
        });
      } else {
        pipelineConfig.duplicatePipeline(pipelineId).then((copiedPipeline) => {
          if (copiedPipeline) {
            focusPipelineEditor();
          }
        });
      }
    },
    [focusPipelineEditor, pipelineConfig],
  );

  const handleNewPipeline = useCallback(() => {
    const initialStageNames = columns.map((column) => column.status.name);

    if (pipelineConfig.isDirty) {
      setUnsavedDialog({
        isOpen: true,
        pendingAction: () => pipelineConfig.newPipeline(initialStageNames),
        description: 'Creating a new pipeline will discard your changes',
      });
    } else {
      pipelineConfig.newPipeline(initialStageNames);
    }
  }, [columns, pipelineConfig]);

  const handleDelete = useCallback(async () => {
    const pipelineId = pipelineConfig.editingPipelineId;
    const pipelineName = pipelineConfig.pipeline?.name ?? 'Pipeline';
    if (!pipelineId || !projectId) return;

    const confirmed = await confirm({
      title: 'Delete Pipeline',
      description: 'Are you sure you want to delete this pipeline?',
      variant: 'danger',
      confirmLabel: 'Delete Pipeline',
    });
    if (confirmed) {
      undoableDelete({
        id: pipelineId,
        entityLabel: `Pipeline: ${pipelineName}`,
        onDelete: async () => {
          await pipelineConfig.deletePipeline();
        },
      });
    }
  }, [pipelineConfig, confirm, projectId, undoableDelete]);

  const handleUnsavedSave = useCallback(async () => {
    const saved = await pipelineConfig.savePipeline();
    const action = unsavedDialog.pendingAction;
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
    if (saved) {
      action?.();
    }
  }, [pipelineConfig, unsavedDialog.pendingAction]);

  const handleUnsavedDiscard = useCallback(() => {
    pipelineConfig.discardChanges();
    const action = unsavedDialog.pendingAction;
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
    action?.();
  }, [pipelineConfig, unsavedDialog.pendingAction]);

  const handleUnsavedCancel = useCallback(() => {
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
  }, []);

  return {
    unsavedDialog,
    blocker,
    isBlocked,
    handleWorkflowSelect,
    handleWorkflowCopy,
    handleNewPipeline,
    handleDelete,
    handleUnsavedSave,
    handleUnsavedDiscard,
    handleUnsavedCancel,
  };
}
