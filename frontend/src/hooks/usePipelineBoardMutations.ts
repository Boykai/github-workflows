/**
 * usePipelineBoardMutations — board-level mutations for pipeline stages and agents.
 *
 * Pure state-update callbacks extracted from usePipelineConfig to keep
 * each hook under 200 lines.
 */

import { useCallback, type Dispatch, type SetStateAction } from 'react';
import { generateId } from '@/utils/generateId';
import type {
  PipelineConfig,
  PipelineStage,
  PipelineAgentNode,
  PipelineModelOverride,
  AvailableAgent,
} from '@/types';

export interface UsePipelineBoardMutationsReturn {
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
  reorderAgentsInStage: (stageId: string, newOrder: PipelineAgentNode[]) => void;
}

export function usePipelineBoardMutations(
  setPipeline: Dispatch<SetStateAction<PipelineConfig | null>>,
  modelOverride: PipelineModelOverride,
  clearValidationError: (field: string) => void,
): UsePipelineBoardMutationsReturn {
  const setPipelineName = useCallback(
    (name: string) => {
      setPipeline((prev) => (prev ? { ...prev, name } : null));
      clearValidationError('name');
    },
    [setPipeline, clearValidationError],
  );

  const setPipelineDescription = useCallback(
    (description: string) => {
      setPipeline((prev) => (prev ? { ...prev, description } : null));
    },
    [setPipeline],
  );

  const setPipelineBlocking = useCallback(
    (blocking: boolean) => {
      setPipeline((prev) => (prev ? { ...prev, blocking } : null));
    },
    [setPipeline],
  );

  const removeStage = useCallback(
    (stageId: string) => {
      setPipeline((prev) => {
        if (!prev) return null;
        const filtered = prev.stages.filter((s) => s.id !== stageId);
        const reordered = filtered.map((s, idx) => ({ ...s, order: idx }));
        return { ...prev, stages: reordered };
      });
    },
    [setPipeline],
  );

  const updateStage = useCallback(
    (stageId: string, updates: Partial<PipelineStage>) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => (s.id === stageId ? { ...s, ...updates } : s)),
        };
      });
    },
    [setPipeline],
  );

  const reorderStages = useCallback(
    (newOrder: PipelineStage[]) => {
      setPipeline((prev) => {
        if (!prev) return null;
        const reindexed = newOrder.map((s, idx) => ({ ...s, order: idx }));
        return { ...prev, stages: reindexed };
      });
    },
    [setPipeline],
  );

  const addAgentToStage = useCallback(
    (stageId: string, agent: AvailableAgent) => {
      setPipeline((prev) => {
        if (!prev) return null;
        const newAgent: PipelineAgentNode = {
          id: generateId(),
          agent_slug: agent.slug,
          agent_display_name: agent.display_name,
          model_id:
            modelOverride.mode === 'specific'
              ? modelOverride.modelId
              : (agent.default_model_id ?? ''),
          model_name:
            modelOverride.mode === 'specific'
              ? modelOverride.modelName
              : (agent.default_model_name ?? ''),
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
    },
    [setPipeline, modelOverride],
  );

  const removeAgentFromStage = useCallback(
    (stageId: string, agentNodeId: string) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) =>
            s.id === stageId ? { ...s, agents: s.agents.filter((a) => a.id !== agentNodeId) } : s,
          ),
        };
      });
    },
    [setPipeline],
  );

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
    [setPipeline],
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
                      : a,
                  ),
                }
              : s,
          ),
        };
      });
    },
    [setPipeline],
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
    [setPipeline],
  );

  const reorderAgentsInStage = useCallback(
    (stageId: string, newOrder: PipelineAgentNode[]) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => (s.id === stageId ? { ...s, agents: newOrder } : s)),
        };
      });
    },
    [setPipeline],
  );

  return {
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
    reorderAgentsInStage,
  };
}
