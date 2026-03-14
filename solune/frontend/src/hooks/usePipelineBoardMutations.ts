/**
 * usePipelineBoardMutations — board-level mutations for pipeline stages and agents.
 *
 * All agent operations now work through groups rather than directly on stage.agents.
 * The stage.agents field is kept in sync for backward compatibility.
 */

import { useCallback, type Dispatch, type SetStateAction } from 'react';
import { generateId } from '@/utils/generateId';
import type {
  PipelineConfig,
  PipelineStage,
  PipelineAgentNode,
  PipelineModelOverride,
  AvailableAgent,
  ExecutionGroup,
} from '@/types';

/** Sync stage.agents from groups for backward compat. */
function syncLegacyAgents(stage: PipelineStage): PipelineStage {
  const allAgents = (stage.groups ?? []).flatMap((g) => g.agents);
  return { ...stage, agents: allAgents };
}

export interface UsePipelineBoardMutationsReturn {
  setPipelineName: (name: string) => void;
  setPipelineDescription: (description: string) => void;
  removeStage: (stageId: string) => void;
  updateStage: (stageId: string, updates: Partial<PipelineStage>) => void;
  reorderStages: (newOrder: PipelineStage[]) => void;
  addAgentToStage: (stageId: string, agent: AvailableAgent, groupId?: string) => void;
  removeAgentFromStage: (stageId: string, agentNodeId: string) => void;
  updateAgentInStage: (
    stageId: string,
    agentNodeId: string,
    updates: Partial<PipelineAgentNode>,
  ) => void;
  updateAgentTools: (stageId: string, agentNodeId: string, toolIds: string[]) => void;
  cloneAgentInStage: (stageId: string, agentNodeId: string) => void;
  reorderAgentsInStage: (stageId: string, newOrder: PipelineAgentNode[]) => void;
  addGroupToStage: (stageId: string) => void;
  removeGroupFromStage: (stageId: string, groupId: string) => void;
  updateGroupExecutionMode: (stageId: string, groupId: string, mode: 'sequential' | 'parallel') => void;
  moveAgentToGroup: (
    fromStageId: string,
    toStageId: string,
    agentNodeId: string,
    toGroupId: string,
    toIndex?: number,
  ) => void;
  reorderAgentsInGroup: (stageId: string, groupId: string, newOrder: PipelineAgentNode[]) => void;
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
    (stageId: string, agent: AvailableAgent, groupId?: string) => {
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
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const groups = s.groups ?? [];
            // Resolve a valid target group: prefer the requested groupId, then fall back to the first group.
            const existingTargetGroup =
              groupId != null ? groups.find((g) => g.id === groupId) : groups[0];
            let updatedGroups;
            if (existingTargetGroup) {
              const targetGroupId = existingTargetGroup.id;
              updatedGroups = groups.map((g) => {
                if (g.id !== targetGroupId) return g;
                return { ...g, agents: [...g.agents, newAgent] };
              });
            } else {
              // No groups exist yet: create a default group to hold the new agent.
              const newGroup: ExecutionGroup = {
                id: generateId(),
                order: 0,
                execution_mode: 'sequential',
                agents: [newAgent],
              };
              updatedGroups = [newGroup];
            }
            return syncLegacyAgents({ ...s, groups: updatedGroups });
          }),
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
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const updatedGroups = (s.groups ?? []).map((g) => ({
              ...g,
              agents: g.agents.filter((a) => a.id !== agentNodeId),
            }));
            return syncLegacyAgents({ ...s, groups: updatedGroups });
          }),
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
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const updatedGroups = (s.groups ?? []).map((g) => ({
              ...g,
              agents: g.agents.map((a) => (a.id === agentNodeId ? { ...a, ...updates } : a)),
            }));
            return syncLegacyAgents({ ...s, groups: updatedGroups });
          }),
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
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const updatedGroups = (s.groups ?? []).map((g) => ({
              ...g,
              agents: g.agents.map((a) =>
                a.id === agentNodeId
                  ? { ...a, tool_ids: toolIds, tool_count: toolIds.length }
                  : a,
              ),
            }));
            return syncLegacyAgents({ ...s, groups: updatedGroups });
          }),
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
            const updatedGroups = (s.groups ?? []).map((g) => {
              const sourceAgent = g.agents.find((a) => a.id === agentNodeId);
              if (!sourceAgent) return g;
              const cloned: PipelineAgentNode = {
                ...structuredClone(sourceAgent),
                id: generateId(),
              };
              return { ...g, agents: [...g.agents, cloned] };
            });
            return syncLegacyAgents({ ...s, groups: updatedGroups });
          }),
        };
      });
    },
    [setPipeline],
  );

  /** Falls back to reordering in first group. Use reorderAgentsInGroup for group-specific reordering. */
  const reorderAgentsInStage = useCallback(
    (stageId: string, newOrder: PipelineAgentNode[]) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const groups = s.groups ?? [];
            if (groups.length === 0) return s;
            const updatedGroups = [{ ...groups[0], agents: newOrder }, ...groups.slice(1)];
            return syncLegacyAgents({ ...s, groups: updatedGroups });
          }),
        };
      });
    },
    [setPipeline],
  );

  const addGroupToStage = useCallback(
    (stageId: string) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const groups = s.groups ?? [];
            const newGroup: ExecutionGroup = {
              id: generateId(),
              order: groups.length,
              execution_mode: 'sequential',
              agents: [],
            };
            return { ...s, groups: [...groups, newGroup] };
          }),
        };
      });
    },
    [setPipeline],
  );

  const removeGroupFromStage = useCallback(
    (stageId: string, groupId: string) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const groups = s.groups ?? [];
            const targetGroup = groups.find((g) => g.id === groupId);
            // Prevent destructive removal of a populated group.
            if (targetGroup && targetGroup.agents && targetGroup.agents.length > 0) {
              return s;
            }
            const filtered = groups.filter((g) => g.id !== groupId);
            const reordered = filtered.map((g, idx) => ({ ...g, order: idx }));
            return syncLegacyAgents({ ...s, groups: reordered });
          }),
        };
      });
    },
    [setPipeline],
  );

  const updateGroupExecutionMode = useCallback(
    (stageId: string, groupId: string, mode: 'sequential' | 'parallel') => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const updatedGroups = (s.groups ?? []).map((g) =>
              g.id === groupId ? { ...g, execution_mode: mode } : g,
            );
            return { ...s, groups: updatedGroups };
          }),
        };
      });
    },
    [setPipeline],
  );

  const moveAgentToGroup = useCallback(
    (
      fromStageId: string,
      toStageId: string,
      agentNodeId: string,
      toGroupId: string,
      toIndex?: number,
    ) => {
      setPipeline((prev) => {
        if (!prev) return null;
        const targetStage = prev.stages.find((s) => s.id === toStageId);
        const hasTargetGroup = (targetStage?.groups ?? []).some((g) => g.id === toGroupId);
        if (!hasTargetGroup) return prev;
        // Find and remove agent from source
        let movedAgent: PipelineAgentNode | null = null;
        let stages = prev.stages.map((s) => {
          if (s.id !== fromStageId) return s;
          const updatedGroups = (s.groups ?? []).map((g) => {
            const agent = g.agents.find((a) => a.id === agentNodeId);
            if (agent) movedAgent = agent;
            return { ...g, agents: g.agents.filter((a) => a.id !== agentNodeId) };
          });
          return syncLegacyAgents({ ...s, groups: updatedGroups });
        });
        if (!movedAgent) return prev;
        // Add agent to target
        stages = stages.map((s) => {
          if (s.id !== toStageId) return s;
          const updatedGroups = (s.groups ?? []).map((g) => {
            if (g.id !== toGroupId) return g;
            const agents = [...g.agents];
            const idx = toIndex !== undefined ? Math.min(toIndex, agents.length) : agents.length;
            agents.splice(idx, 0, movedAgent!);
            return { ...g, agents };
          });
          return syncLegacyAgents({ ...s, groups: updatedGroups });
        });
        return { ...prev, stages };
      });
    },
    [setPipeline],
  );

  const reorderAgentsInGroup = useCallback(
    (stageId: string, groupId: string, newOrder: PipelineAgentNode[]) => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const updatedGroups = (s.groups ?? []).map((g) =>
              g.id === groupId ? { ...g, agents: newOrder } : g,
            );
            return syncLegacyAgents({ ...s, groups: updatedGroups });
          }),
        };
      });
    },
    [setPipeline],
  );

  return {
    setPipelineName,
    setPipelineDescription,
    removeStage,
    updateStage,
    reorderStages,
    addAgentToStage,
    removeAgentFromStage,
    updateAgentInStage,
    updateAgentTools,
    cloneAgentInStage,
    reorderAgentsInStage,
    addGroupToStage,
    removeGroupFromStage,
    updateGroupExecutionMode,
    moveAgentToGroup,
    reorderAgentsInGroup,
  };
}
