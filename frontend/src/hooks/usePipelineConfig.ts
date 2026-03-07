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
  AvailableAgent,
} from '@/types';

// ── Query Keys ──

export const pipelineKeys = {
  all: ['pipelines'] as const,
  list: (projectId: string) => [...pipelineKeys.all, 'list', projectId] as const,
  detail: (projectId: string, pipelineId: string) =>
    [...pipelineKeys.all, 'detail', projectId, pipelineId] as const,
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

  // Pipeline list
  pipelines: PipelineConfigListResponse | null;
  pipelinesLoading: boolean;

  // Pipeline actions
  newPipeline: () => void;
  loadPipeline: (pipelineId: string) => Promise<void>;
  savePipeline: () => Promise<void>;
  deletePipeline: () => Promise<void>;
  discardChanges: () => void;

  // Board mutations
  setPipelineName: (name: string) => void;
  setPipelineDescription: (description: string) => void;
  addStage: (name?: string) => void;
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
}

// ── Hook ──

export function usePipelineConfig(projectId: string | null): UsePipelineConfigReturn {
  const queryClient = useQueryClient();

  // Pipeline list query
  const { data: pipelines, isLoading: pipelinesLoading } =
    useQuery<PipelineConfigListResponse>({
      queryKey: pipelineKeys.list(projectId ?? ''),
      queryFn: () => pipelinesApi.list(projectId!),
      staleTime: STALE_TIME_SHORT,
      enabled: !!projectId,
    });

  // Local board state
  const [boardState, setBoardState] = useState<PipelineBoardState>('empty');
  const [pipeline, setPipeline] = useState<PipelineConfig | null>(null);
  const [editingPipelineId, setEditingPipelineId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Saved snapshot for isDirty comparison
  const savedSnapshotRef = useRef<string | null>(null);

  const isDirty = useMemo(() => {
    if (!pipeline) return false;
    const currentSnapshot = JSON.stringify({
      name: pipeline.name,
      description: pipeline.description,
      stages: pipeline.stages,
    });
    return currentSnapshot !== savedSnapshotRef.current;
  }, [pipeline]);

  // ── Save snapshot helper ──
  const updateSnapshot = useCallback((config: PipelineConfig) => {
    savedSnapshotRef.current = JSON.stringify({
      name: config.name,
      description: config.description,
      stages: config.stages,
    });
  }, []);

  // ── Pipeline Actions ──

  const newPipeline = useCallback(() => {
    const now = new Date().toISOString();
    const newConfig: PipelineConfig = {
      id: '',
      projectId: projectId ?? '',
      name: '',
      description: '',
      stages: [],
      createdAt: now,
      updatedAt: now,
      // snake_case fields for API compatibility
      project_id: projectId ?? '',
      created_at: now,
      updated_at: now,
    } as PipelineConfig;
    setPipeline(newConfig);
    setEditingPipelineId(null);
    setBoardState('creating');
    savedSnapshotRef.current = JSON.stringify({
      name: '',
      description: '',
      stages: [],
    });
  }, [projectId]);

  const loadPipeline = useCallback(
    async (pipelineId: string) => {
      if (!projectId) return;
      try {
        const config = await pipelinesApi.get(projectId, pipelineId);
        setPipeline(config);
        setEditingPipelineId(pipelineId);
        setBoardState('editing');
        updateSnapshot(config);
        setSaveError(null);
      } catch (err) {
        setSaveError(err instanceof Error ? err.message : 'Failed to load pipeline');
      }
    },
    [projectId, updateSnapshot],
  );

  const savePipeline = useCallback(async () => {
    if (!pipeline || !projectId) return;
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
        });
      } else {
        // Create new
        saved = await pipelinesApi.create(projectId, {
          name: pipeline.name,
          description: pipeline.description,
          stages: pipeline.stages,
        });
      }
      setPipeline(saved);
      setEditingPipelineId(saved.id);
      setBoardState('editing');
      updateSnapshot(saved);
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save pipeline');
    } finally {
      setIsSaving(false);
    }
  }, [pipeline, projectId, editingPipelineId, updateSnapshot, queryClient]);

  const deletePipeline = useCallback(async () => {
    if (!editingPipelineId || !projectId) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await pipelinesApi.delete(projectId, editingPipelineId);
      setPipeline(null);
      setEditingPipelineId(null);
      setBoardState('empty');
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
        prev ? { ...prev, name: saved.name, description: saved.description, stages: saved.stages } : null,
      );
    } else {
      // New pipeline — reset to empty
      setPipeline(null);
      setEditingPipelineId(null);
      setBoardState('empty');
      savedSnapshotRef.current = null;
    }
    setSaveError(null);
  }, [editingPipelineId]);

  // ── Board Mutations ──

  const setPipelineName = useCallback((name: string) => {
    setPipeline((prev) => (prev ? { ...prev, name } : null));
  }, []);

  const setPipelineDescription = useCallback((description: string) => {
    setPipeline((prev) => (prev ? { ...prev, description } : null));
  }, []);

  const addStage = useCallback((name?: string) => {
    setPipeline((prev) => {
      if (!prev) return null;
      const newStage: PipelineStage = {
        id: generateId(),
        name: name ?? `Stage ${prev.stages.length + 1}`,
        order: prev.stages.length,
        agents: [],
      };
      return { ...prev, stages: [...prev.stages, newStage] };
    });
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
        model_id: '',
        model_name: '',
        config: {},
      };
      return {
        ...prev,
        stages: prev.stages.map((s) =>
          s.id === stageId ? { ...s, agents: [...s.agents, newAgent] } : s,
        ),
      };
    });
  }, []);

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

  return {
    boardState,
    pipeline,
    editingPipelineId,
    isDirty,
    isSaving,
    saveError,
    pipelines: pipelines ?? null,
    pipelinesLoading,
    newPipeline,
    loadPipeline,
    savePipeline,
    deletePipeline,
    discardChanges,
    setPipelineName,
    setPipelineDescription,
    addStage,
    removeStage,
    updateStage,
    reorderStages,
    addAgentToStage,
    removeAgentFromStage,
    updateAgentInStage,
  };
}
