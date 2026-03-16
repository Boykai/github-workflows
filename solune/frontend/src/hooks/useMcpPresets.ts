import { useQuery } from '@tanstack/react-query';
import { toolsApi, ApiError } from '@/services/api';
import type { McpPresetListResponse } from '@/types';

export const mcpPresetKeys = {
  all: ['mcp-presets'] as const,
};

export function useMcpPresets() {
  const query = useQuery<McpPresetListResponse, ApiError>({
    queryKey: mcpPresetKeys.all,
    queryFn: () => toolsApi.listPresets(),
    staleTime: Infinity,
  });

  return {
    presets: query.data?.presets ?? [],
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    rawError: query.error ?? null,
    refetch: query.refetch,
  };
}
