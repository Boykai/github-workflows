/**
 * useWorkflow Hook
 *
 * Provides TanStack Query mutations for confirming/rejecting
 * AI-generated recommendations and managing workflow configuration.
 * Uses the centralized API client from services/api.ts.
 */

import { useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowApi } from '@/services/api';
import type { WorkflowResult, WorkflowConfiguration } from '@/types';

interface UseWorkflowReturn {
  confirmRecommendation: (recommendationId: string) => Promise<WorkflowResult>;
  rejectRecommendation: (recommendationId: string) => Promise<void>;
  getConfig: () => Promise<WorkflowConfiguration>;
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

  const getConfigMutation = useMutation({
    mutationFn: () => workflowApi.getConfig(),
  });

  const updateConfigMutation = useMutation({
    mutationFn: (config: Partial<WorkflowConfiguration>) =>
      workflowApi.updateConfig(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow', 'config'] });
    },
  });

  const isLoading =
    confirmMutation.isPending ||
    rejectMutation.isPending ||
    getConfigMutation.isPending ||
    updateConfigMutation.isPending;

  const error =
    confirmMutation.error?.message ??
    rejectMutation.error?.message ??
    getConfigMutation.error?.message ??
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
    () => getConfigMutation.mutateAsync(),
    [getConfigMutation],
  );

  const updateConfig = useCallback(
    (config: Partial<WorkflowConfiguration>) => updateConfigMutation.mutateAsync(config),
    [updateConfigMutation],
  );

  return {
    confirmRecommendation,
    rejectRecommendation,
    getConfig,
    updateConfig,
    isLoading,
    error,
  };
}
