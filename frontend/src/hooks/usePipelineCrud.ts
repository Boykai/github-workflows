/** CRUD operations for pipeline configs (create, load, save, copy, delete, assign). */

import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import { generateId } from '@/utils/generateId';
import { pipelineKeys } from './usePipelineOrchestration';
import type { PipelineConfig, PipelineConfigCreate } from '@/types';
import type { PipelineAction } from './usePipelineReducer';

const errMsg = (e: unknown, fallback: string) =>
  e instanceof Error ? e.message : fallback;

// Our enriched PipelineStage is a strict superset of the generated schema type.
const buildPayload = (p: PipelineConfig) => ({
  name: p.name, description: p.description, stages: p.stages,
}) as PipelineConfigCreate;

interface CrudArgs {
  projectId: string | null;
  pipeline: PipelineConfig | null;
  editingPipelineId: string | null;
  dispatch: React.Dispatch<PipelineAction>;
  validatePipeline: () => boolean;
  resetPending: () => void;
}

export function usePipelineCrud({
  projectId, pipeline, editingPipelineId, dispatch, validatePipeline, resetPending,
}: CrudArgs) {
  const queryClient = useQueryClient();

  const assignPipeline = useCallback(async (pipelineId: string) => {
    if (!projectId) return;
    try {
      const result = await pipelinesApi.setAssignment(projectId, pipelineId);
      queryClient.setQueryData(pipelineKeys.assignment(projectId), result);
      await queryClient.invalidateQueries({ queryKey: pipelineKeys.assignment(projectId) });
    } catch (err) { console.warn('Pipeline assignment failed:', err); }
  }, [projectId, queryClient]);

  const newPipeline = useCallback((stageNames: string[] = []) => {
    const now = new Date().toISOString();
    const stages = stageNames.map((n, i) => ({
      id: generateId(), name: n, order: i,
      execution_mode: 'sequential' as const,
      groups: [{ id: generateId(), order: 0, execution_mode: 'sequential' as const, agents: [] }],
      agents: [],
    }));
    const config: PipelineConfig = {
      id: '', project_id: projectId ?? '', name: '', description: '', stages,
      is_preset: false, preset_id: '', created_at: now, updated_at: now,
    };
    dispatch({ type: 'NEW_PIPELINE', config });
    resetPending();
  }, [projectId, resetPending, dispatch]);

  const loadPipeline = useCallback(async (pipelineId: string) => {
    if (!projectId) return;
    try {
      const config = await pipelinesApi.get(projectId, pipelineId);
      dispatch({ type: 'LOAD_SUCCESS', config, id: pipelineId });
      resetPending();
    } catch (err) { dispatch({ type: 'SET_ERROR', error: errMsg(err, 'Failed to load pipeline') }); }
  }, [projectId, resetPending, dispatch]);

  const savePipeline = useCallback(async () => {
    if (!pipeline || !projectId) return false;
    if (!validatePipeline()) return false;
    if (editingPipelineId && pipeline.is_preset) {
      dispatch({ type: 'SET_ERROR', error: "Preset pipelines can't be overwritten." });
      return false;
    }
    dispatch({ type: 'SAVE_START' });
    try {
      const saved = editingPipelineId
        ? await pipelinesApi.update(projectId, editingPipelineId, buildPayload(pipeline))
        : await pipelinesApi.create(projectId, buildPayload(pipeline));
      dispatch({ type: 'SAVE_SUCCESS', config: saved });
      await queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
      return true;
    } catch (err) { dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to save pipeline') }); return false; }
  }, [pipeline, editingPipelineId, projectId, validatePipeline, queryClient, dispatch]);

  const saveAsCopy = useCallback(async (newName: string) => {
    if (!pipeline || !projectId) return;
    dispatch({ type: 'SAVE_START' });
    try {
      const saved = await pipelinesApi.create(projectId, { ...buildPayload(pipeline), name: newName });
      dispatch({ type: 'SAVE_SUCCESS', config: saved });
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) { dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to save copy') }); }
  }, [pipeline, projectId, queryClient, dispatch]);

  const deletePipeline = useCallback(async () => {
    if (!editingPipelineId || !projectId) return;
    dispatch({ type: 'SAVE_START' });
    try {
      await pipelinesApi.delete(projectId, editingPipelineId);
      dispatch({ type: 'DELETE_SUCCESS' });
      resetPending();
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) { dispatch({ type: 'SAVE_FAILURE', error: errMsg(err, 'Failed to delete pipeline') }); }
  }, [editingPipelineId, projectId, queryClient, resetPending, dispatch]);

  return { assignPipeline, newPipeline, loadPipeline, savePipeline, saveAsCopy, deletePipeline };
}
