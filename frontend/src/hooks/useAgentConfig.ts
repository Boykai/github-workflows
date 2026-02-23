/**
 * useAgentConfig Hook
 *
 * Manages local agent_mappings state cloned from server config.
 * Provides isDirty flag, per-column dirty detection, and CRUD operations.
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { AgentAssignment, WorkflowConfiguration, AvailableAgent } from '@/types';
import { useWorkflow } from './useWorkflow';
import { generateId } from '@/utils/generateId';
import { workflowApi } from '@/services/api';

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
  /** Reorder agents within a column */
  reorderAgents: (status: string, newOrder: AgentAssignment[]) => void;
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
  const { getConfig, updateConfig } = useWorkflow();
  const [serverConfig, setServerConfig] = useState<WorkflowConfiguration | null>(null);
  const [localMappings, setLocalMappings] = useState<Record<string, AgentAssignment[]>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const serverMappingsRef = useRef<Record<string, AgentAssignment[]>>({});

  const loadConfig = useCallback(async () => {
    if (!projectId) return;
    try {
      const config = await getConfig();
      setServerConfig(config);
      const mappings = config.agent_mappings ?? {};
      serverMappingsRef.current = mappings;
      setLocalMappings(structuredClone(mappings));
      setIsLoaded(true);
    } catch {
      // Error handled by useWorkflow
    }
  }, [projectId, getConfig]);

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
      const current = prev[status] ?? [];
      const newAssignment: AgentAssignment = {
        id: generateId(),
        slug: agent.slug,
        display_name: agent.display_name,
      };
      return { ...prev, [status]: [...current, newAssignment] };
    });
  }, []);

  const removeAgent = useCallback((status: string, agentInstanceId: string) => {
    setLocalMappings((prev) => {
      const current = prev[status] ?? [];
      return { ...prev, [status]: current.filter((a) => a.id !== agentInstanceId) };
    });
  }, []);

  const reorderAgents = useCallback((status: string, newOrder: AgentAssignment[]) => {
    setLocalMappings((prev) => ({ ...prev, [status]: newOrder }));
  }, []);

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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save';
      setSaveError(message);
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
    reorderAgents,
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

interface UseAvailableAgentsReturn {
  agents: AvailableAgent[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAvailableAgents(projectId?: string | null): UseAvailableAgentsReturn {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
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
    agents: data ?? [],
    isLoading,
    error: error?.message ?? null,
    refetch,
  };
}
