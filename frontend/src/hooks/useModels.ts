/**
 * useModels — fetch and cache available AI models with provider grouping.
 */

import { useQuery } from '@tanstack/react-query';
import { modelsApi } from '@/services/api';
import { STALE_TIME_LONG } from '@/constants';
import type { AIModel, ModelGroup } from '@/types';
import { useMemo } from 'react';

export function useModels() {
  const { data, isLoading, error } = useQuery<AIModel[]>({
    queryKey: ['models'],
    queryFn: () => modelsApi.list(''),
    staleTime: STALE_TIME_LONG,
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
    error: error ? (error as Error).message : null,
  };
}
