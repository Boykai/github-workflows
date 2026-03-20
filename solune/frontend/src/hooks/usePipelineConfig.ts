/** Core pipeline state management hook — composes sub-hooks + useReducer for CRUD. */

import { useReducer, useCallback, useMemo, useEffect, useRef, useState, type SetStateAction } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { pipelinesApi } from '@/services/api';
import { STALE_TIME_SHORT } from '@/constants';
import { generateId } from '@/utils/generateId';
import { usePipelineBoardMutations } from './usePipelineBoardMutations';
import { usePipelineValidation } from './usePipelineValidation';
import { usePipelineModelOverride } from './usePipelineModelOverride';
import { pipelineReducer, initialState, computeSnapshot } from './usePipelineReducer';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import type { PipelineConfig, PipelineConfigListResponse, PaginatedResponse, PipelineConfigSummary } from '@/types';

const MAX_UNDO_STACK = 50;

const errMsg = (e: unknown, fallback: string) =>
  e instanceof Error ? e.message : fallback;

const buildPayload = (p: PipelineConfig) => ({
  name: p.name, description: p.description, stages: p.stages,
});

const buildCopyName = (sourceName: string, existingNames: string[]) => {
  const trimmedSourceName = sourceName.trim() || 'Untitled Pipeline';
  const normalizedNames = new Set(existingNames.map((name) => name.trim().toLowerCase()));
  const baseCopyName = `${trimmedSourceName} (Copy)`;

  if (!normalizedNames.has(baseCopyName.toLowerCase())) {
    return baseCopyName;
  }

  let copyIndex = 2;
  while (normalizedNames.has(`${trimmedSourceName} (Copy ${copyIndex})`.toLowerCase())) {
    copyIndex += 1;
  }

  return `${trimmedSourceName} (Copy ${copyIndex})`;
};

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

  // ── Undo / Redo ──
  const undoStackRef = useRef<PipelineConfig[]>([]);
  const redoStackRef = useRef<PipelineConfig[]>([]);
  const lastSnapshotRef = useRef<string | null>(null);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);

  const pushUndoSnapshot = useCallback((pipeline: PipelineConfig) => {
    const snap = computeSnapshot(pipeline);
    if (snap === lastSnapshotRef.current) return;
    undoStackRef.current = [...undoStackRef.current.slice(-(MAX_UNDO_STACK - 1)), pipeline];
    redoStackRef.current = [];
    lastSnapshotRef.current = snap;
    setCanUndo(true);
    setCanRedo(false);
  }, []);

  const clearUndoRedo = useCallback(() => {
    undoStackRef.current = [];
    redoStackRef.current = [];
    lastSnapshotRef.current = null;
    setCanUndo(false);
    setCanRedo(false);
  }, []);

  const setPipeline = useCallback(
    (updater: SetStateAction<PipelineConfig | null>) =>
      dispatch({ type: 'SET_PIPELINE', updater }),
    [],
  );

  const setPipelineWithUndo = useCallback(
    (updater: SetStateAction<PipelineConfig | null>) => {
      if (state.pipeline) pushUndoSnapshot(state.pipeline);
      dispatch({ type: 'SET_PIPELINE', updater });
    },
    [state.pipeline, pushUndoSnapshot],
  );

  const undo = useCallback(() => {
    if (undoStackRef.current.length === 0 || !state.pipeline) return;
    const previous = undoStackRef.current[undoStackRef.current.length - 1];
    undoStackRef.current = undoStackRef.current.slice(0, -1);
    redoStackRef.current = [...redoStackRef.current, state.pipeline];
    lastSnapshotRef.current = computeSnapshot(previous);
    setCanUndo(undoStackRef.current.length > 0);
    setCanRedo(true);
    dispatch({ type: 'SET_PIPELINE', updater: previous });
  }, [state.pipeline]);

  const redo = useCallback(() => {
    if (redoStackRef.current.length === 0 || !state.pipeline) return;
    const next = redoStackRef.current[redoStackRef.current.length - 1];
    redoStackRef.current = redoStackRef.current.slice(0, -1);
    undoStackRef.current = [...undoStackRef.current, state.pipeline];
    lastSnapshotRef.current = computeSnapshot(next);
    setCanUndo(true);
    setCanRedo(redoStackRef.current.length > 0);
    dispatch({ type: 'SET_PIPELINE', updater: next });
  }, [state.pipeline]);

  // Keyboard shortcuts: Ctrl+Z / Cmd+Z = undo, Ctrl+Shift+Z / Cmd+Shift+Z = redo
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      if (!mod || e.key.toLowerCase() !== 'z') return;
      // Don't intercept when focused on text inputs
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      e.preventDefault();
      if (e.shiftKey) {
        redo();
      } else {
        undo();
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [undo, redo]);

  const { validationErrors, validatePipeline, clearValidationError } =
    usePipelineValidation(state.pipeline);
  const { modelOverride, setModelOverride, resetPending } = usePipelineModelOverride(
    state.pipeline,
    setPipeline,
  );
  const boardMutations = usePipelineBoardMutations(
    setPipelineWithUndo, modelOverride, clearValidationError,
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
      toast.success('Pipeline assigned');
    } catch (err) {
      console.warn('Pipeline assignment failed:', err);
      toast.error(errMsg(err, 'Failed to assign pipeline'), { duration: Infinity });
    }
  }, [projectId, queryClient]);

  const newPipeline = useCallback((stageNames: string[] = []) => {
    const now = new Date().toISOString();
    const stages = stageNames.map((n, i) => ({
      id: generateId(),
      name: n,
      order: i,
      groups: [{ id: generateId(), order: 0, execution_mode: 'sequential' as const, agents: [] }],
      agents: [],
    }));
    const config: PipelineConfig = {
      id: '', project_id: projectId ?? '', name: '', description: '', stages,
      is_preset: false, preset_id: '', created_at: now, updated_at: now,
    };
    dispatch({ type: 'NEW_PIPELINE', config });
    clearUndoRedo();
    resetPending();
  }, [projectId, clearUndoRedo, resetPending]);

  const loadPipeline = useCallback(async (pipelineId: string) => {
    if (!projectId) return;
    try {
      const config = await pipelinesApi.get(projectId, pipelineId);
      dispatch({ type: 'LOAD_SUCCESS', config, id: pipelineId });
      clearUndoRedo();
      resetPending();
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: errMsg(err, 'Failed to load pipeline') });
    }
  }, [projectId, clearUndoRedo, resetPending]);

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
      toast.success('Pipeline saved');
      return true;
    } catch (err) {
      dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to save pipeline') });
      toast.error(errMsg(err, 'Failed to save pipeline'), { duration: Infinity });
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
      toast.success('Pipeline saved as copy');
    } catch (err) {
      dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to save copy') });
      toast.error(errMsg(err, 'Failed to save copy'), { duration: Infinity });
    }
  }, [state.pipeline, projectId, queryClient]);

  const existingPipelineNames = useMemo(
    () => (pipelines?.pipelines ?? []).map((pipeline) => pipeline.name),
    [pipelines?.pipelines]
  );

  const duplicatePipeline = useCallback(async (pipelineId: string) => {
    if (!projectId) return null;
    dispatch({ type: 'SAVE_START' });
    try {
      const source = await pipelinesApi.get(projectId, pipelineId);
      const copyName = buildCopyName(
        source.name,
        existingPipelineNames,
      );
      const saved = await pipelinesApi.create(projectId, {
        ...buildPayload(source),
        name: copyName,
      });
      dispatch({ type: 'SAVE_SUCCESS', config: saved });
      await queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
      toast.success('Pipeline duplicated');
      return saved;
    } catch (err) {
      dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to copy pipeline') });
      toast.error(errMsg(err, 'Failed to copy pipeline'), { duration: Infinity });
      return null;
    }
  }, [existingPipelineNames, projectId, queryClient]);

  const deletePipeline = useCallback(async () => {
    if (!state.editingPipelineId || !projectId) return;
    dispatch({ type: 'SAVE_START' });

    // Optimistic: remove the pipeline from the list cache immediately
    const listQueryKey = pipelineKeys.list(projectId);
    await queryClient.cancelQueries({ queryKey: listQueryKey });
    const listSnapshot = queryClient.getQueryData<PipelineConfigListResponse>(listQueryKey);
    if (listSnapshot) {
      queryClient.setQueryData<PipelineConfigListResponse>(listQueryKey, (old) => {
        if (!old) return old;
        return {
          ...old,
          pipelines: old.pipelines.filter((p) => p.id !== state.editingPipelineId),
        };
      });
    }

    try {
      await pipelinesApi.delete(projectId, state.editingPipelineId);
      dispatch({ type: 'DELETE_SUCCESS' });
      clearUndoRedo();
      resetPending();
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) {
      const message = errMsg(err, 'Failed to delete pipeline');
      // Rollback optimistic update
      if (listSnapshot) {
        queryClient.setQueryData(listQueryKey, listSnapshot);
      }
      dispatch({ type: 'SAVE_FAILURE', error: message });
      toast.error(message, { duration: Infinity });
      throw err instanceof Error ? err : new Error(message);
    } finally {
      queryClient.invalidateQueries({ queryKey: listQueryKey });
    }
  }, [state.editingPipelineId, projectId, queryClient, clearUndoRedo, resetPending]);

  const discardChanges = useCallback(() => {
    if (state.editingPipelineId && state.savedSnapshot) {
      dispatch({ type: 'DISCARD_EDITING' });
    } else {
      dispatch({ type: 'DISCARD_NEW' });
      resetPending();
    }
    clearUndoRedo();
  }, [state.editingPipelineId, state.savedSnapshot, clearUndoRedo, resetPending]);

  const setStageExecutionMode = useCallback(
    (stageId: string, mode: 'sequential' | 'parallel') => {
      setPipelineWithUndo((prev) => {
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
    [setPipelineWithUndo]
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
    savePipeline, saveAsCopy, duplicatePipeline, deletePipeline, discardChanges,
    setStageExecutionMode,
    canUndo, canRedo, undo, redo,
    ...boardMutations,
  };
}

/** Standalone paginated pipeline list hook for infinite scroll use cases. */
export function usePipelineListPaginated(projectId: string | null) {
  const queryClient = useQueryClient();
  const result = useInfiniteList<PipelineConfigSummary>({
    queryKey: [...pipelineKeys.list(projectId ?? ''), 'paginated'],
    queryFn: async (params) => {
      const resp = await pipelinesApi.listPaginated(projectId!, params);
      return {
        items: resp.pipelines,
        next_cursor: resp.next_cursor,
        has_more: resp.has_more,
        total_count: resp.total_count,
      } as PaginatedResponse<PipelineConfigSummary>;
    },
    limit: 20,
    staleTime: STALE_TIME_SHORT,
    enabled: !!projectId,
  });

  return {
    ...result,
    invalidate: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
      }
    },
  };
}
