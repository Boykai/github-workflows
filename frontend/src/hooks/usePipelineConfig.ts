/** Core pipeline state management hook — composes sub-hooks + useReducer for CRUD. */

import { useReducer, useCallback } from 'react';
import { usePipelineBoardMutations } from './usePipelineBoardMutations';
import { usePipelineValidation } from './usePipelineValidation';
import { usePipelineModelOverride } from './usePipelineModelOverride';
import { pipelineReducer, initialState } from './usePipelineReducer';
import { usePipelineOrchestration } from './usePipelineOrchestration';
import { usePipelineCrud } from './usePipelineCrud';
import { usePipelineDirtyState } from './usePipelineDirtyState';
import type { PipelineConfig } from '@/types';

export { pipelineKeys } from './usePipelineOrchestration';

export function usePipelineConfig(projectId: string | null) {
  const [state, dispatch] = useReducer(pipelineReducer, initialState);

  const setPipeline = useCallback(
    (updater: React.SetStateAction<PipelineConfig | null>) =>
      dispatch({ type: 'SET_PIPELINE', updater }),
    [],
  );

  const { validationErrors, validatePipeline, clearValidationError } =
    usePipelineValidation(state.pipeline);
  const { modelOverride, setModelOverride, resetPending } = usePipelineModelOverride(
    state.pipeline,
    setPipeline,
  );
  const boardMutations = usePipelineBoardMutations(
    setPipeline, modelOverride, clearValidationError,
  );

  const { pipelines, pipelinesLoading, assignedPipelineId, setStageExecutionMode } =
    usePipelineOrchestration(projectId, setPipeline);

  const { assignPipeline, newPipeline, loadPipeline, savePipeline, saveAsCopy, deletePipeline } =
    usePipelineCrud({
      projectId,
      pipeline: state.pipeline,
      editingPipelineId: state.editingPipelineId,
      dispatch,
      validatePipeline,
      resetPending,
    });

  const { isDirty, discardChanges } = usePipelineDirtyState({
    pipeline: state.pipeline,
    savedSnapshot: state.savedSnapshot,
    editingPipelineId: state.editingPipelineId,
    boardState: state.boardState,
    dispatch,
    resetPending,
  });

  return {
    boardState: state.boardState, pipeline: state.pipeline,
    editingPipelineId: state.editingPipelineId, isDirty,
    isSaving: state.isSaving, saveError: state.saveError,
    isPreset: state.pipeline?.is_preset ?? false,
    modelOverride, setModelOverride,
    validationErrors, validatePipeline, clearValidationError,
    pipelines, pipelinesLoading, assignedPipelineId,
    assignPipeline, newPipeline, loadPipeline,
    savePipeline, saveAsCopy, deletePipeline, discardChanges,
    setStageExecutionMode,
    ...boardMutations,
  };
}
