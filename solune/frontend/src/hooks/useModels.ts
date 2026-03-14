/**
 * useModels — fetch and cache available AI models with provider grouping.
 */

import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { modelsApi } from '@/services/api';
import type { AIModel, ModelGroup } from '@/types';

export const modelKeys = {
  all: ['models'] as const,
  copilot: () => [...modelKeys.all, 'copilot'] as const,
};

export async function fetchCopilotModels(forceRefresh = false): Promise<AIModel[]> {
  return modelsApi.list(forceRefresh);
}

export function useModels() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery<AIModel[]>({
    queryKey: modelKeys.copilot(),
    queryFn: () => fetchCopilotModels(false),
    staleTime: Infinity,
    gcTime: Infinity,
    retry: 2,
  });

  const refreshMutation = useMutation({
    mutationFn: () => fetchCopilotModels(true),
    onSuccess: (freshModels) => {
      queryClient.setQueryData(modelKeys.copilot(), freshModels);
    },
  });

  const models = useMemo(() => data ?? [], [data]);

  const modelsByProvider = useMemo<ModelGroup[]>(() => {
    const groups = new Map<string, AIModel[]>();
    for (const model of models) {
      const existing = groups.get(model.provider) ?? [];
      existing.push(model);
      groups.set(model.provider, existing);
    }
    return Array.from(groups.entries()).map(([provider, providerModels]) => ({
      provider,
      models: providerModels,
    }));
  }, [models]);

  return {
    models,
    modelsByProvider,
    isLoading,
    isRefreshing: refreshMutation.isPending,
    refreshModels: () => refreshMutation.mutateAsync(),
    error: error ? (error as Error).message : null,
  };
}
