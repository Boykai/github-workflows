/**
 * useWorkflow Hook
 *
 * Provides TanStack Query mutations for confirming/rejecting
 * AI-generated recommendations and managing workflow configuration.
 * Config fetching uses useQuery for proper caching and dedup.
 * Uses the centralized API client from services/api.ts.
 */

import { useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { workflowApi } from '@/services/api';
import type { WorkflowResult, WorkflowConfiguration } from '@/types';

interface UseWorkflowReturn {
  confirmRecommendation: (recommendationId: string) => Promise<WorkflowResult>;
  rejectRecommendation: (recommendationId: string) => Promise<void>;
  /** Imperatively (re-)fetch the workflow config. Backed by useQuery cache. */
  getConfig: () => Promise<WorkflowConfiguration>;
  /** Cached config data (may be undefined until first fetch). */
  config: WorkflowConfiguration | undefined;
  updateConfig: (config: Partial<WorkflowConfiguration>) => Promise<WorkflowConfiguration>;
  isLoading: boolean;
  error: string | null;
}

export function useWorkflow(): UseWorkflowReturn {
  const queryClient = useQueryClient();

  const confirmMutation = useMutation({
    mutationFn: (recommendationId: string) =>
      workflowApi.confirmRecommendation(recommendationId),
  });

  const rejectMutation = useMutation({
    mutationFn: (recommendationId: string) =>
      workflowApi.rejectRecommendation(recommendationId),
  });

  const configQuery = useQuery({
    queryKey: ['workflow', 'config'],
    queryFn: () => workflowApi.getConfig(),
    staleTime: 60_000,
    enabled: false, // only fetch on demand via refetch / getConfig
  });

  const updateConfigMutation = useMutation({
    mutationFn: (config: Partial<WorkflowConfiguration>) =>
      workflowApi.updateConfig(config as WorkflowConfiguration),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow', 'config'] });
    },
  });

  const isLoading =
    confirmMutation.isPending ||
    rejectMutation.isPending ||
    configQuery.isFetching ||
    updateConfigMutation.isPending;

  const error =
    confirmMutation.error?.message ??
    rejectMutation.error?.message ??
    configQuery.error?.message ??
    updateConfigMutation.error?.message ??
    null;

  const confirmRecommendation = useCallback(
    (recommendationId: string) => confirmMutation.mutateAsync(recommendationId),
    [confirmMutation],
  );

  const rejectRecommendation = useCallback(
    (recommendationId: string) => rejectMutation.mutateAsync(recommendationId),
    [rejectMutation],
  );

  const getConfig = useCallback(
    async (): Promise<WorkflowConfiguration> => {
      const result = await configQuery.refetch();
      if (result.error) throw result.error;
      return result.data!;
    },
    [configQuery],
  );

  const updateConfig = useCallback(
    (config: Partial<WorkflowConfiguration>) => updateConfigMutation.mutateAsync(config),
    [updateConfigMutation],
  );

  return {
    confirmRecommendation,
    rejectRecommendation,
    getConfig,
    config: configQuery.data,
    updateConfig,
    isLoading,
    error,
  };
}
