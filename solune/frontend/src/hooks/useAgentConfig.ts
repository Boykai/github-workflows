/**
 * useAgentConfig Hook
 *
 * Manages local agent_mappings state cloned from server config.
 * Provides isDirty flag, per-column dirty detection, and CRUD operations.
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import type { AgentAssignment, WorkflowConfiguration, AvailableAgent } from '@/types';
import { useWorkflow } from './useWorkflow';
import { generateId } from '@/utils/generateId';
import { workflowApi } from '@/services/api';
import { caseInsensitiveKey } from '@/lib/case-utils';

interface UseAgentConfigReturn {
  /** Local agent mappings state (editable) */
  localMappings: Record<string, AgentAssignment[]>;
  /** Whether there are unsaved changes */
  isDirty: boolean;
  /** Check if a specific column has been modified */
  isColumnDirty: (status: string) => boolean;
  /** Add an agent to a status column */
  addAgent: (status: string, agent: AvailableAgent) => void;
  /** Remove an agent by instance ID */
  removeAgent: (status: string, agentInstanceId: string) => void;
  /** Clone an agent assignment within a status column */
  cloneAgent: (status: string, agentInstanceId: string) => void;
  /** Reorder agents within a column */
  reorderAgents: (status: string, newOrder: AgentAssignment[]) => void;
  /** Move an agent from one column to another */
  moveAgentToColumn: (
    sourceStatus: string,
    targetStatus: string,
    agentId: string,
    targetIndex?: number
  ) => void;
  /** Apply a preset configuration */
  applyPreset: (mappings: Record<string, AgentAssignment[]>) => void;
  /** Save changes to server */
  save: () => Promise<void>;
  /** Discard local changes */
  discard: () => void;
  /** Whether save is in progress */
  isSaving: boolean;
  /** Save error message */
  saveError: string | null;
  /** Whether config has been loaded */
  isLoaded: boolean;
  /** Load config from server */
  loadConfig: () => Promise<void>;
}

export function useAgentConfig(projectId?: string | null): UseAgentConfigReturn {
  const { updateConfig } = useWorkflow();
  const queryClient = useQueryClient();
  const [serverConfig, setServerConfig] = useState<WorkflowConfiguration | null>(null);
  const [localMappings, setLocalMappings] = useState<Record<string, AgentAssignment[]>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const serverMappingsRef = useRef<Record<string, AgentAssignment[]>>({});

  // Stable loadConfig that only depends on projectId (not an unstable getConfig ref).
  // The old version captured `getConfig` from useWorkflow which changed identity every
  // render (it closes over the useQuery result object), causing an infinite re-render
  // loop: loadConfig changes → useEffect fires → setState → re-render → repeat.
  const loadConfig = useCallback(async () => {
    if (!projectId) return;
    try {
      const result = await queryClient.fetchQuery({
        queryKey: ['workflow', 'config'],
        queryFn: () => workflowApi.getConfig(),
        staleTime: 60_000,
      });
      setServerConfig(result);
      // Deduplicate case-variant status keys from the server response.
      // GitHub project column names may differ in casing from backend
      // defaults (e.g. "In progress" vs "In Progress"). Merge duplicates
      // so only one entry per case-insensitive status name is kept.
      const rawMappings = result.agent_mappings ?? {};
      const deduped: Record<string, AgentAssignment[]> = {};
      const seen = new Map<string, string>(); // lowercase → chosen key
      for (const [key, agents] of Object.entries(rawMappings)) {
        const lower = key.toLowerCase();
        const existingKey = seen.get(lower);
        if (existingKey === undefined) {
          seen.set(lower, key);
          deduped[key] = agents;
        } else if (
          (!deduped[existingKey] || deduped[existingKey].length === 0) &&
          agents.length > 0
        ) {
          // Replace the empty entry with the populated one
          delete deduped[existingKey];
          seen.set(lower, key);
          deduped[key] = agents;
        }
        // else keep existing (already has agents, or both empty)
      }
      serverMappingsRef.current = deduped;
      setLocalMappings(structuredClone(deduped));
      setIsLoaded(true);
    } catch {
      // Error handled by useWorkflow
    }
  }, [projectId, queryClient]);

  // Load config when projectId changes
  useEffect(() => {
    if (projectId) {
      loadConfig();
    } else {
      setServerConfig(null);
      setLocalMappings({});
      serverMappingsRef.current = {};
      setIsLoaded(false);
    }
  }, [projectId, loadConfig]);

  const isDirty = useMemo(() => {
    const server = serverMappingsRef.current;
    const statuses = new Set([...Object.keys(server), ...Object.keys(localMappings)]);
    for (const status of statuses) {
      const serverAgents = server[status] ?? [];
      const localAgents = localMappings[status] ?? [];
      if (serverAgents.length !== localAgents.length) return true;
      for (let i = 0; i < serverAgents.length; i++) {
        if (serverAgents[i].slug !== localAgents[i].slug) return true;
      }
    }
    return false;
  }, [localMappings]);

  const isColumnDirty = useCallback(
    (status: string): boolean => {
      const serverAgents = serverMappingsRef.current[status] ?? [];
      const localAgents = localMappings[status] ?? [];
      if (serverAgents.length !== localAgents.length) return true;
      for (let i = 0; i < serverAgents.length; i++) {
        if (serverAgents[i].slug !== localAgents[i].slug) return true;
      }
      return false;
    },
    [localMappings]
  );

  const addAgent = useCallback((status: string, agent: AvailableAgent) => {
    setLocalMappings((prev) => {
      // Find existing key with case-insensitive match to avoid creating
      // duplicate entries like "In Progress" and "In progress".
      const matchedKey = caseInsensitiveKey(prev, status);
      const current = prev[matchedKey] ?? [];
      const newAssignment: AgentAssignment = {
        id: generateId(),
        slug: agent.slug,
        display_name: agent.display_name,
        config:
          agent.default_model_id || agent.default_model_name
            ? {
                model_id: agent.default_model_id ?? '',
                model_name: agent.default_model_name ?? '',
              }
            : null,
      };
      // Use the board's column name (status) as the canonical key
      const updated = { ...prev, [status]: [...current, newAssignment] };
      // Remove the old key if it has different casing
      if (matchedKey !== status) {
        delete updated[matchedKey];
      }
      return updated;
    });
  }, []);

  const removeAgent = useCallback((status: string, agentInstanceId: string) => {
    setLocalMappings((prev) => {
      // Case-insensitive key lookup
      const matchedKey = caseInsensitiveKey(prev, status);
      const current = prev[matchedKey] ?? [];
      return { ...prev, [matchedKey]: current.filter((a) => a.id !== agentInstanceId) };
    });
  }, []);

  const cloneAgent = useCallback((status: string, agentInstanceId: string) => {
    setLocalMappings((prev) => {
      const matchedKey = caseInsensitiveKey(prev, status);
      const current = prev[matchedKey] ?? [];
      const sourceIndex = current.findIndex((agent) => agent.id === agentInstanceId);
      if (sourceIndex === -1) {
        return prev;
      }

      const sourceAgent = current[sourceIndex];
      const clonedAssignment: AgentAssignment = {
        ...sourceAgent,
        id: generateId(),
      };
      const nextAgents = [...current];
      nextAgents.splice(sourceIndex + 1, 0, clonedAssignment);

      return { ...prev, [matchedKey]: nextAgents };
    });
  }, []);

  const reorderAgents = useCallback((status: string, newOrder: AgentAssignment[]) => {
    setLocalMappings((prev) => {
      // Case-insensitive key lookup
      const matchedKey = caseInsensitiveKey(prev, status);
      const updated = { ...prev, [status]: newOrder };
      if (matchedKey !== status) {
        delete updated[matchedKey];
      }
      return updated;
    });
  }, []);

  const moveAgentToColumn = useCallback(
    (sourceStatus: string, targetStatus: string, agentId: string, targetIndex?: number) => {
      setLocalMappings((prev) => {
        // Case-insensitive key lookup for source
        const sourceKey = caseInsensitiveKey(prev, sourceStatus);
        const sourceAgents = prev[sourceKey] ?? [];

        const agentIndex = sourceAgents.findIndex((a) => a.id === agentId);
        if (agentIndex === -1) return prev; // No-op if not found

        const agent = sourceAgents[agentIndex];

        const targetKey = caseInsensitiveKey(prev, targetStatus);

        // Guard against same-column moves to avoid duplicating the agent
        if (sourceKey === targetKey) {
          const working = [...sourceAgents];
          working.splice(agentIndex, 1);
          const insertAt =
            targetIndex !== undefined
              ? Math.min(Math.max(0, targetIndex), working.length)
              : working.length;
          working.splice(insertAt, 0, agent);
          return { ...prev, [sourceKey]: working };
        }

        const newSource = [...sourceAgents];
        newSource.splice(agentIndex, 1);

        const targetAgents = [...(prev[targetKey] ?? [])];

        // Clamp target index
        const insertAt =
          targetIndex !== undefined
            ? Math.min(Math.max(0, targetIndex), targetAgents.length)
            : targetAgents.length;
        targetAgents.splice(insertAt, 0, agent);

        return { ...prev, [sourceKey]: newSource, [targetKey]: targetAgents };
      });
    },
    []
  );

  const applyPreset = useCallback((mappings: Record<string, AgentAssignment[]>) => {
    setLocalMappings((prev) => {
      // Merge preset into existing statuses, keeping any status not in preset as empty
      const result: Record<string, AgentAssignment[]> = {};
      const allStatuses = new Set([...Object.keys(prev), ...Object.keys(mappings)]);
      for (const status of allStatuses) {
        result[status] = mappings[status] ?? [];
      }
      return result;
    });
  }, []);

  const save = useCallback(async () => {
    if (!serverConfig) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      const updatedConfig = await updateConfig({
        ...serverConfig,
        agent_mappings: localMappings,
      });
      const mappings = updatedConfig.agent_mappings ?? {};
      serverMappingsRef.current = mappings;
      setLocalMappings(structuredClone(mappings));
      setServerConfig(updatedConfig);
      toast.success('Agent configuration saved');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save';
      setSaveError(message);
      toast.error(message, { duration: Infinity });
    } finally {
      setIsSaving(false);
    }
  }, [serverConfig, localMappings, updateConfig]);

  const discard = useCallback(() => {
    setLocalMappings(structuredClone(serverMappingsRef.current));
    setSaveError(null);
  }, []);

  return {
    localMappings,
    isDirty,
    isColumnDirty,
    addAgent,
    removeAgent,
    cloneAgent,
    reorderAgents,
    moveAgentToColumn,
    applyPreset,
    save,
    discard,
    isSaving,
    saveError,
    isLoaded,
    loadConfig,
  };
}

// ============ useAvailableAgents Hook (T018) ============

/** Stable empty array to avoid creating new references each render. */
const EMPTY_AGENTS: AvailableAgent[] = [];

interface UseAvailableAgentsReturn {
  agents: AvailableAgent[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAvailableAgents(projectId?: string | null): UseAvailableAgentsReturn {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['workflow', 'agents', projectId],
    queryFn: async () => {
      const result = await workflowApi.listAgents();
      return result.agents ?? [];
    },
    enabled: !!projectId,
    staleTime: Infinity,
    gcTime: 10 * 60 * 1000,
  });

  return {
    agents: data ?? EMPTY_AGENTS,
    isLoading,
    error: error?.message ?? null,
    refetch,
  };
}
