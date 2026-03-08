/**
 * useTools — TanStack Query hooks for MCP tool CRUD operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toolsApi, ApiError } from '@/services/api';
import type {
  McpToolConfig,
  McpToolConfigCreate,
  McpToolConfigUpdate,
  McpToolConfigListResponse,
  McpToolSyncResult,
  ToolDeleteResult,
} from '@/types';

export const toolKeys = {
  all: ['tools'] as const,
  list: (projectId: string) => [...toolKeys.all, 'list', projectId] as const,
  detail: (projectId: string, toolId: string) =>
    [...toolKeys.all, 'detail', projectId, toolId] as const,
};

const STALE_TIME_TOOLS = 30_000; // 30 seconds

export function useToolsList(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const query = useQuery<McpToolConfigListResponse>({
    queryKey: toolKeys.list(projectId ?? ''),
    queryFn: () => toolsApi.list(projectId!),
    staleTime: STALE_TIME_TOOLS,
    enabled: !!projectId,
  });

  const uploadMutation = useMutation<McpToolConfig, ApiError, McpToolConfigCreate>({
    mutationFn: (data) => toolsApi.create(projectId!, data),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
    },
  });

  const syncMutation = useMutation<McpToolSyncResult, ApiError, string>({
    mutationFn: (toolId) => {
      setSyncingId(toolId);
      return toolsApi.sync(projectId!, toolId);
    },
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
    },
    onSettled: () => setSyncingId(null),
  });

  const updateMutation = useMutation<
    McpToolConfig,
    ApiError,
    { toolId: string; data: McpToolConfigUpdate }
  >({
    mutationFn: ({ toolId, data }) => toolsApi.update(projectId!, toolId, data),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
    },
  });

  const deleteMutation = useMutation<
    ToolDeleteResult,
    ApiError,
    { toolId: string; confirm?: boolean }
  >({
    mutationFn: ({ toolId, confirm }) => {
      setDeletingId(toolId);
      return toolsApi.delete(projectId!, toolId, confirm);
    },
    onSuccess: (result) => {
      if (result.success && projectId) {
        queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
      }
    },
    onSettled: () => setDeletingId(null),
  });

  const authError =
    query.error instanceof ApiError && query.error.status === 401;

  return {
    tools: query.data?.tools ?? [],
    isLoading: query.isLoading,
    error: query.error ? (query.error as Error).message : null,

    uploadTool: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error?.message ?? null,
    resetUploadError: uploadMutation.reset,

    syncTool: syncMutation.mutateAsync,
    syncingId,
    syncError: syncMutation.error?.message ?? null,

    updateTool: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error?.message ?? null,
    resetUpdateError: updateMutation.reset,

    deleteTool: deleteMutation.mutateAsync,
    deletingId,
    deleteError: deleteMutation.error?.message ?? null,
    deleteResult: deleteMutation.data ?? null,

    authError,
  };
}
