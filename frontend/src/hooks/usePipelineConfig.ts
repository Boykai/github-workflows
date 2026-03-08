/**
 * usePipelineConfig — core state management hook for pipeline CRUD.
 *
 * Manages board state (empty/creating/editing), local working copy,
 * isDirty tracking, and CRUD operations via TanStack Query mutations.
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import { STALE_TIME_SHORT } from '@/constants';
import { generateId } from '@/utils/generateId';
import type {
  PipelineConfig,
  PipelineStage,
  PipelineAgentNode,
  PipelineBoardState,
  PipelineConfigListResponse,
  PipelineModelOverride,
  PipelineValidationErrors,
  AvailableAgent,
} from '@/types';

// ── Query Keys ──

export const pipelineKeys = {
  all: ['pipelines'] as const,
  list: (projectId: string) => [...pipelineKeys.all, 'list', projectId] as const,
  detail: (projectId: string, pipelineId: string) =>
    [...pipelineKeys.all, 'detail', projectId, pipelineId] as const,
  assignment: (projectId: string) =>
    [...pipelineKeys.all, 'assignment', projectId] as const,
};

// ── Return Type ──

interface UsePipelineConfigReturn {
  // State
  boardState: PipelineBoardState;
  pipeline: PipelineConfig | null;
  editingPipelineId: string | null;
  isDirty: boolean;
  isSaving: boolean;
  saveError: string | null;
  isPreset: boolean;

  // Model override
  modelOverride: PipelineModelOverride;
  setModelOverride: (override: PipelineModelOverride) => void;

  // Validation
  validationErrors: PipelineValidationErrors;
  validatePipeline: () => boolean;
  clearValidationError: (field: string) => void;

  // Pipeline list
  pipelines: PipelineConfigListResponse | null;
  pipelinesLoading: boolean;

  // Pipeline assignment
  assignedPipelineId: string;
  assignPipeline: (pipelineId: string) => Promise<void>;

  // Pipeline actions
  newPipeline: (stageNames?: string[]) => void;
  loadPipeline: (pipelineId: string) => Promise<void>;
  savePipeline: () => Promise<boolean>;
  saveAsCopy: (newName: string) => Promise<void>;
  deletePipeline: () => Promise<void>;
  discardChanges: () => void;

  // Board mutations
  setPipelineName: (name: string) => void;
  setPipelineDescription: (description: string) => void;
  setPipelineBlocking: (blocking: boolean) => void;
  removeStage: (stageId: string) => void;
  updateStage: (stageId: string, updates: Partial<PipelineStage>) => void;
  reorderStages: (newOrder: PipelineStage[]) => void;
  addAgentToStage: (stageId: string, agent: AvailableAgent) => void;
  removeAgentFromStage: (stageId: string, agentNodeId: string) => void;
  updateAgentInStage: (
    stageId: string,
    agentNodeId: string,
    updates: Partial<PipelineAgentNode>,
  ) => void;
  updateAgentTools: (stageId: string, agentNodeId: string, toolIds: string[]) => void;
  cloneAgentInStage: (stageId: string, agentNodeId: string) => void;
}

// ── Hook ──

export function usePipelineConfig(projectId: string | null): UsePipelineConfigReturn {
  const queryClient = useQueryClient();

  const deriveModelOverride = useCallback((config: PipelineConfig | null): PipelineModelOverride => {
    if (!config) {
      return { mode: 'auto', modelId: '', modelName: '' };
    }

    const agents = config.stages.flatMap((stage) => stage.agents);
    if (agents.length === 0) {
      return { mode: 'auto', modelId: '', modelName: '' };
    }

    const uniqueModels = [...new Set(agents.map((agent) => agent.model_id || ''))];
    if (uniqueModels.length === 1) {
      const modelId = uniqueModels[0];
      if (!modelId) {
        return { mode: 'auto', modelId: '', modelName: '' };
      }

      const matchingAgent = agents.find((agent) => agent.model_id === modelId);
      return {
        mode: 'specific',
        modelId,
        modelName: matchingAgent?.model_name ?? '',
      };
    }

    return { mode: 'mixed', modelId: '', modelName: '' };
  }, []);

  const buildStage = useCallback((name: string, order: number): PipelineStage => ({
    id: generateId(),
    name,
    order,
    agents: [],
  }), []);

  // Pipeline list query
  const { data: pipelines, isLoading: pipelinesLoading } =
    useQuery<PipelineConfigListResponse>({
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

  // Local board state
  const [boardState, setBoardState] = useState<PipelineBoardState>('empty');
  const [pipeline, setPipeline] = useState<PipelineConfig | null>(null);
  const [editingPipelineId, setEditingPipelineId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<PipelineValidationErrors>({});
  const [pendingModelOverride, setPendingModelOverride] = useState<PipelineModelOverride | null>(null);

  // Saved snapshot for isDirty comparison
  const savedSnapshotRef = useRef<string | null>(null);

  const isDirty = useMemo(() => {
    if (!pipeline) return false;
    const currentSnapshot = JSON.stringify({
      name: pipeline.name,
      description: pipeline.description,
      stages: pipeline.stages,
      blocking: pipeline.blocking,
    });
    return currentSnapshot !== savedSnapshotRef.current;
  }, [pipeline]);

  const isPreset = useMemo(() => pipeline?.is_preset ?? false, [pipeline]);
  const hasAnyAgents = useMemo(
    () => (pipeline?.stages.some((stage) => stage.agents.length > 0) ?? false),
    [pipeline],
  );
  const modelOverride = useMemo(() => {
    const derived = deriveModelOverride(pipeline);
    if (hasAnyAgents) return derived;
    return pendingModelOverride ?? derived;
  }, [deriveModelOverride, hasAnyAgents, pendingModelOverride, pipeline]);
  const assignedPipelineId = assignment?.pipeline_id ?? '';

  // ── Save snapshot helper ──
  const updateSnapshot = useCallback((config: PipelineConfig) => {
    savedSnapshotRef.current = JSON.stringify({
      name: config.name,
      description: config.description,
      stages: config.stages,
      blocking: config.blocking,
    });
  }, []);

  // ── Validation ──
  const validatePipeline = useCallback((): boolean => {
    const errors: PipelineValidationErrors = {};
    if (!pipeline?.name?.trim()) {
      errors.name = 'Pipeline name is required';
    }
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [pipeline]);

  const clearValidationError = useCallback((field: string) => {
    setValidationErrors((prev) => {
      if (!prev[field]) return prev;
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  // ── Model Override ──
  const setModelOverride = useCallback((override: PipelineModelOverride) => {
    setPendingModelOverride(override);
    setPipeline((prev) => {
      if (!prev) return null;
      const updatedStages = prev.stages.map((stage) => ({
        ...stage,
        agents: stage.agents.map((agent) => ({
          ...agent,
          model_id: override.mode === 'specific' ? override.modelId : '',
          model_name: override.mode === 'specific' ? override.modelName : '',
        })),
      }));
      return { ...prev, stages: updatedStages };
    });
  }, []);

  // ── Pipeline Assignment ──
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

  // ── Pipeline Actions ──

  const newPipeline = useCallback((stageNames: string[] = []) => {
    const now = new Date().toISOString();
    const seededStages = stageNames.map((stageName, index) => buildStage(stageName, index));
    const newConfig: PipelineConfig = {
      id: '',
      project_id: projectId ?? '',
      name: '',
      description: '',
      stages: seededStages,
      is_preset: false,
      preset_id: '',
      blocking: false,
      created_at: now,
      updated_at: now,
    };
    setPipeline(newConfig);
    setEditingPipelineId(null);
    setBoardState('creating');
    setPendingModelOverride(null);
    setValidationErrors({});
    savedSnapshotRef.current = JSON.stringify({
      name: '',
      description: '',
      stages: seededStages,
      blocking: false,
    });
  }, [buildStage, projectId]);

  const loadPipeline = useCallback(
    async (pipelineId: string) => {
      if (!projectId) return;
      try {
        const config = await pipelinesApi.get(projectId, pipelineId);
        setPipeline(config);
        setEditingPipelineId(pipelineId);
        setBoardState('editing');
        setPendingModelOverride(null);
        updateSnapshot(config);
        setSaveError(null);
        setValidationErrors({});
      } catch (err) {
        setSaveError(err instanceof Error ? err.message : 'Failed to load pipeline');
      }
    },
    [projectId, updateSnapshot],
  );

  const savePipeline = useCallback(async () => {
    if (!pipeline || !projectId) return false;
    if (!validatePipeline()) return false;
    if (editingPipelineId && pipeline.is_preset) {
      setSaveError("Preset pipelines can't be overwritten. Use Save as Copy.");
      return false;
    }

    setIsSaving(true);
    setSaveError(null);
    try {
      let saved: PipelineConfig;
      if (editingPipelineId) {
        // Update existing
        saved = await pipelinesApi.update(projectId, editingPipelineId, {
          name: pipeline.name,
          description: pipeline.description,
          stages: pipeline.stages,
          blocking: pipeline.blocking,
        });
      } else {
        // Create new
        saved = await pipelinesApi.create(projectId, {
          name: pipeline.name,
          description: pipeline.description,
          stages: pipeline.stages,
          blocking: pipeline.blocking,
        });
      }
      setPipeline(saved);
      setEditingPipelineId(saved.id);
      setBoardState('editing');
      setValidationErrors({});
      updateSnapshot(saved);
      // Invalidate list
      await queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
      return true;
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save pipeline');
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [pipeline, projectId, editingPipelineId, updateSnapshot, queryClient, validatePipeline]);

  const saveAsCopy = useCallback(async (newName: string) => {
    if (!pipeline || !projectId) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      const saved = await pipelinesApi.create(projectId, {
        name: newName,
        description: pipeline.description,
        stages: pipeline.stages,
        blocking: pipeline.blocking,
      });
      setPipeline(saved);
      setEditingPipelineId(saved.id);
      setBoardState('editing');
      updateSnapshot(saved);
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save pipeline copy');
    } finally {
      setIsSaving(false);
    }
  }, [pipeline, projectId, updateSnapshot, queryClient]);

  const deletePipeline = useCallback(async () => {
    if (!editingPipelineId || !projectId) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await pipelinesApi.delete(projectId, editingPipelineId);
      setPipeline(null);
      setEditingPipelineId(null);
      setBoardState('empty');
      setPendingModelOverride(null);
      savedSnapshotRef.current = null;
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to delete pipeline');
    } finally {
      setIsSaving(false);
    }
  }, [editingPipelineId, projectId, queryClient]);

  const discardChanges = useCallback(() => {
    if (editingPipelineId && savedSnapshotRef.current) {
      // Revert to saved state
      const saved = JSON.parse(savedSnapshotRef.current);
      setPipeline((prev) =>
        prev ? { ...prev, name: saved.name, description: saved.description, stages: saved.stages, blocking: saved.blocking ?? false } : null,
      );
    } else {
      // New pipeline — reset to empty
      setPipeline(null);
      setEditingPipelineId(null);
      setBoardState('empty');
      setPendingModelOverride(null);
      savedSnapshotRef.current = null;
    }
    setSaveError(null);
    setValidationErrors({});
  }, [editingPipelineId]);

  // ── Board Mutations ──

  const setPipelineName = useCallback((name: string) => {
    setPipeline((prev) => (prev ? { ...prev, name } : null));
    clearValidationError('name');
  }, [clearValidationError]);

  const setPipelineDescription = useCallback((description: string) => {
    setPipeline((prev) => (prev ? { ...prev, description } : null));
  }, []);

  const setPipelineBlocking = useCallback((blocking: boolean) => {
    setPipeline((prev) => (prev ? { ...prev, blocking } : null));
  }, []);

  const removeStage = useCallback((stageId: string) => {
    setPipeline((prev) => {
      if (!prev) return null;
      const filtered = prev.stages.filter((s) => s.id !== stageId);
      // Re-index order
      const reordered = filtered.map((s, idx) => ({ ...s, order: idx }));
      return { ...prev, stages: reordered };
    });
  }, []);

  const updateStage = useCallback((stageId: string, updates: Partial<PipelineStage>) => {
    setPipeline((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        stages: prev.stages.map((s) => (s.id === stageId ? { ...s, ...updates } : s)),
      };
    });
  }, []);

  const reorderStages = useCallback((newOrder: PipelineStage[]) => {
    setPipeline((prev) => {
      if (!prev) return null;
      const reindexed = newOrder.map((s, idx) => ({ ...s, order: idx }));
      return { ...prev, stages: reindexed };
    });
  }, []);

  const addAgentToStage = useCallback((stageId: string, agent: AvailableAgent) => {
    setPipeline((prev) => {
      if (!prev) return null;
      const newAgent: PipelineAgentNode = {
        id: generateId(),
        agent_slug: agent.slug,
        agent_display_name: agent.display_name,
        model_id: modelOverride.mode === 'specific' ? modelOverride.modelId : (agent.default_model_id ?? ''),
        model_name: modelOverride.mode === 'specific' ? modelOverride.modelName : (agent.default_model_name ?? ''),
        tool_ids: [],
        tool_count: 0,
        config: {},
      };
      return {
        ...prev,
        stages: prev.stages.map((s) =>
          s.id === stageId ? { ...s, agents: [...s.agents, newAgent] } : s,
        ),
      };
    });
  }, [modelOverride]);

  const removeAgentFromStage = useCallback((stageId: string, agentNodeId: string) => {
    setPipeline((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        stages: prev.stages.map((s) =>
          s.id === stageId
            ? { ...s, agents: s.agents.filter((a) => a.id !== agentNodeId) }
            : s,
        ),
      };
    });
  }, []);

  const updateAgentInStage = useCallback(
    (stageId: string, agentNodeId: string, updates: Partial<PipelineAgentNode>) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) =>
            s.id === stageId
              ? {
                  ...s,
                  agents: s.agents.map((a) => (a.id === agentNodeId ? { ...a, ...updates } : a)),
                }
              : s,
          ),
        };
      });
    },
    [],
  );

  const updateAgentTools = useCallback(
    (stageId: string, agentNodeId: string, toolIds: string[]) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) =>
            s.id === stageId
              ? {
                  ...s,
                  agents: s.agents.map((a) =>
                    a.id === agentNodeId
                      ? { ...a, tool_ids: toolIds, tool_count: toolIds.length }
                      : a
                  ),
                }
              : s,
          ),
        };
      });
    },
    [],
  );

  const cloneAgentInStage = useCallback(
    (stageId: string, agentNodeId: string) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const sourceAgent = s.agents.find((a) => a.id === agentNodeId);
            if (!sourceAgent) return s;
            const cloned: PipelineAgentNode = {
              ...structuredClone(sourceAgent),
              id: generateId(),
            };
            return { ...s, agents: [...s.agents, cloned] };
          }),
        };
      });
    },
    [],
  );

  return {
    boardState,
    pipeline,
    editingPipelineId,
    isDirty,
    isSaving,
    saveError,
    isPreset,
    modelOverride,
    setModelOverride,
    validationErrors,
    validatePipeline,
    clearValidationError,
    pipelines: pipelines ?? null,
    pipelinesLoading,
    assignedPipelineId,
    assignPipeline,
    newPipeline,
    loadPipeline,
    savePipeline,
    saveAsCopy,
    deletePipeline,
    discardChanges,
    setPipelineName,
    setPipelineDescription,
    setPipelineBlocking,
    removeStage,
    updateStage,
    reorderStages,
    addAgentToStage,
    removeAgentFromStage,
    updateAgentInStage,
    updateAgentTools,
    cloneAgentInStage,
  };
}
