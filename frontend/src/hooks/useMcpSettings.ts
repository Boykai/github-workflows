/**
 * Custom hook for managing MCP configuration state via TanStack Query.
 *
 * Provides queries for listing MCPs and mutations for creating/deleting,
 * plus 401 auth error detection for re-authentication prompts.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { mcpApi, ApiError } from '@/services/api';
import { STALE_TIME_LONG } from '@/constants';
import type {
  McpConfigurationListResponse,
  McpConfigurationCreate,
  McpConfiguration,
} from '@/types';

// ── Query Keys ──

export const mcpKeys = {
  all: ['mcp'] as const,
  list: () => [...mcpKeys.all, 'list'] as const,
};

// ── Hook ──

export function useMcpSettings() {
  const queryClient = useQueryClient();
  // Track which specific MCP ID is currently being deleted so that only
  // that list item shows the "Removing…" indicator, not all of them.
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // List MCPs
  const query = useQuery<McpConfigurationListResponse>({
    queryKey: mcpKeys.list(),
    queryFn: mcpApi.listMcps,
    staleTime: STALE_TIME_LONG,
  });

  // Create MCP mutation
  const createMutation = useMutation<McpConfiguration, Error, McpConfigurationCreate>({
    mutationFn: (data) => mcpApi.createMcp(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mcpKeys.list() });
    },
  });

  // Delete MCP mutation — wraps mutateAsync to track the target ID
  const deleteMutation = useMutation<{ message: string }, Error, string>({
    mutationFn: (mcpId) => mcpApi.deleteMcp(mcpId),
    onMutate: (mcpId) => {
      setDeletingId(mcpId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mcpKeys.list() });
    },
    onSettled: () => {
      setDeletingId(null);
    },
  });

  // Detect 401 auth errors from any operation
  const authError =
    (query.error instanceof ApiError && query.error.status === 401) ||
    (createMutation.error instanceof ApiError && createMutation.error.status === 401) ||
    (deleteMutation.error instanceof ApiError && deleteMutation.error.status === 401);

  return {
    mcps: query.data?.mcps ?? [],
    count: query.data?.count ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,

    createMcp: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    resetCreateError: createMutation.reset,

    deleteMcp: deleteMutation.mutateAsync,
    deletingId,
    deleteError: deleteMutation.error,
    resetDeleteError: deleteMutation.reset,

    authError,
  };
}
