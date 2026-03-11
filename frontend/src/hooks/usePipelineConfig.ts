/** Core pipeline state management hook — composes sub-hooks + useReducer for CRUD. */

import { useReducer, useCallback, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import { STALE_TIME_SHORT } from '@/constants';
import { generateId } from '@/utils/generateId';
import { usePipelineBoardMutations } from './usePipelineBoardMutations';
import { usePipelineValidation } from './usePipelineValidation';
import { usePipelineModelOverride } from './usePipelineModelOverride';
import { pipelineReducer, initialState, computeSnapshot } from './usePipelineReducer';
import type { PipelineConfig, PipelineConfigListResponse } from '@/types';

const errMsg = (e: unknown, fallback: string) =>
  e instanceof Error ? e.message : fallback;

const buildPayload = (p: PipelineConfig) => ({
  name: p.name, description: p.description, stages: p.stages, blocking: p.blocking,
});

export const pipelineKeys = {
  all: ['pipelines'] as const,
  list: (projectId: string) => [...pipelineKeys.all, 'list', projectId] as const,
  detail: (projectId: string, pipelineId: string) =>
    [...pipelineKeys.all, 'detail', projectId, pipelineId] as const,
  assignment: (projectId: string) => [...pipelineKeys.all, 'assignment', projectId] as const,
};

export function usePipelineConfig(projectId: string | null) {
  const queryClient = useQueryClient();
  const [state, dispatch] = useReducer(pipelineReducer, initialState);

  const setPipeline = useCallback(
    (updater: React.SetStateAction<PipelineConfig | null>) =>
      dispatch({ type: 'SET_PIPELINE', updater }),
    [],
  );

  const { validationErrors, validatePipeline, clearValidationError } =
    usePipelineValidation(state.pipeline);
  const { modelOverride, setModelOverride, _resetPending } = usePipelineModelOverride(
    state.pipeline,
    setPipeline,
  ) as ReturnType<typeof usePipelineModelOverride> & { _resetPending: () => void };
  const boardMutations = usePipelineBoardMutations(
    setPipeline, modelOverride, clearValidationError,
  );

  const { data: pipelines, isLoading: pipelinesLoading } = useQuery<PipelineConfigListResponse>({
    queryKey: pipelineKeys.list(projectId ?? ''),
    queryFn: () => pipelinesApi.list(projectId!),
    staleTime: STALE_TIME_SHORT,
    enabled: !!projectId,
  });
  const { data: assignment } = useQuery({
    queryKey: pipelineKeys.assignment(projectId ?? ''),
    queryFn: () => pipelinesApi.getAssignment(projectId!),
    enabled: !!projectId,
    staleTime: STALE_TIME_SHORT,
  });

  const isDirty = useMemo(() => {
    if (!state.pipeline) return false;
    return computeSnapshot(state.pipeline) !== state.savedSnapshot;
  }, [state.pipeline, state.savedSnapshot]);

  const assignPipeline = useCallback(async (pipelineId: string) => {
    if (!projectId) return;
    try {
      const result = await pipelinesApi.setAssignment(projectId, pipelineId);
      queryClient.setQueryData(pipelineKeys.assignment(projectId), result);
      await queryClient.invalidateQueries({ queryKey: pipelineKeys.assignment(projectId) });
    } catch (err) {
      console.warn('Pipeline assignment failed:', err);
    }
  }, [projectId, queryClient]);

  const newPipeline = useCallback((stageNames: string[] = []) => {
    const now = new Date().toISOString();
    const stages = stageNames.map((n, i) => ({ id: generateId(), name: n, order: i, agents: [] }));
    const config: PipelineConfig = {
      id: '', project_id: projectId ?? '', name: '', description: '', stages,
      is_preset: false, preset_id: '', blocking: false, created_at: now, updated_at: now,
    };
    dispatch({ type: 'NEW_PIPELINE', config });
    _resetPending();
  }, [projectId, _resetPending]);

  const loadPipeline = useCallback(async (pipelineId: string) => {
    if (!projectId) return;
    try {
      const config = await pipelinesApi.get(projectId, pipelineId);
      dispatch({ type: 'LOAD_SUCCESS', config, id: pipelineId });
      _resetPending();
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: errMsg(err, 'Failed to load pipeline') });
    }
  }, [projectId, _resetPending]);

  const savePipeline = useCallback(async () => {
    if (!state.pipeline || !projectId) return false;
    if (!validatePipeline()) return false;
    if (state.editingPipelineId && state.pipeline.is_preset) {
      dispatch({ type: 'SET_ERROR', error: "Preset pipelines can't be overwritten." });
      return false;
    }
    dispatch({ type: 'SAVE_START' });
    try {
      const saved = state.editingPipelineId
        ? await pipelinesApi.update(projectId, state.editingPipelineId, buildPayload(state.pipeline))
        : await pipelinesApi.create(projectId, buildPayload(state.pipeline));
      dispatch({ type: 'SAVE_SUCCESS', config: saved });
      await queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
      return true;
    } catch (err) {
      dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to save pipeline') });
      return false;
    }
  }, [state.pipeline, state.editingPipelineId, projectId, validatePipeline, queryClient]);

  const saveAsCopy = useCallback(async (newName: string) => {
    if (!state.pipeline || !projectId) return;
    dispatch({ type: 'SAVE_START' });
    try {
      const saved = await pipelinesApi.create(projectId, { ...buildPayload(state.pipeline), name: newName });
      dispatch({ type: 'SAVE_SUCCESS', config: saved });
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) {
      dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to save copy') });
    }
  }, [state.pipeline, projectId, queryClient]);

  const deletePipeline = useCallback(async () => {
    if (!state.editingPipelineId || !projectId) return;
    dispatch({ type: 'SAVE_START' });
    try {
      await pipelinesApi.delete(projectId, state.editingPipelineId);
      dispatch({ type: 'DELETE_SUCCESS' });
      _resetPending();
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) {
      dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to delete pipeline') });
    }
  }, [state.editingPipelineId, projectId, queryClient, _resetPending]);

  const discardChanges = useCallback(() => {
    if (state.editingPipelineId && state.savedSnapshot) {
      dispatch({ type: 'DISCARD_EDITING' });
    } else {
      dispatch({ type: 'DISCARD_NEW' });
      _resetPending();
    }
  }, [state.editingPipelineId, state.savedSnapshot, _resetPending]);

  const setStageExecutionMode = useCallback(
    (stageId: string, mode: 'sequential' | 'parallel') => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            // Only allow parallel if there are 2+ agents
            const effectiveMode = mode === 'parallel' && s.agents.length < 2 ? 'sequential' : mode;
            return { ...s, execution_mode: effectiveMode };
          }),
        };
      });
    },
    []
  );

  return {
    boardState: state.boardState, pipeline: state.pipeline,
    editingPipelineId: state.editingPipelineId, isDirty,
    isSaving: state.isSaving, saveError: state.saveError,
    isPreset: state.pipeline?.is_preset ?? false,
    modelOverride, setModelOverride,
    validationErrors, validatePipeline, clearValidationError,
    pipelines: pipelines ?? null, pipelinesLoading,
    assignedPipelineId: assignment?.pipeline_id ?? '',
    assignPipeline, newPipeline, loadPipeline,
    savePipeline, saveAsCopy, deletePipeline, discardChanges,
    setStageExecutionMode,
    ...boardMutations,
  };
}
