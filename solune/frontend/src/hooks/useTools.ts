/**
 * useTools — TanStack Query hooks for MCP tool CRUD operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toolsApi, ApiError } from '@/services/api';
import { repoMcpKeys } from '@/hooks/useRepoMcpConfig';
import { agentKeys } from '@/hooks/useAgents';
import { isRateLimitApiError } from '@/utils/rateLimit';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { useUndoableDelete } from '@/hooks/useUndoableDelete';
import type {
  McpToolConfig,
  McpToolConfigCreate,
  McpToolConfigUpdate,
  McpToolConfigListResponse,
  McpToolSyncResult,
  PaginatedResponse,
} from '@/types';

function formatMutationError(error: unknown, action: string): string {
  if (isRateLimitApiError(error)) {
    return `Could not ${action}. Rate limit reached. Please wait a few minutes before retrying.`;
  }
  const message = error instanceof Error ? error.message : 'An unexpected error occurred';
  return `Could not ${action}. ${message}. Please try again.`;
}

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

  const query = useQuery<McpToolConfigListResponse, ApiError>({
    queryKey: toolKeys.list(projectId ?? ''),
    queryFn: () => toolsApi.list(projectId!),
    staleTime: STALE_TIME_TOOLS,
    enabled: !!projectId,
  });

  const uploadMutation = useMutation<McpToolConfig, ApiError, McpToolConfigCreate>({
    mutationFn: (data) => toolsApi.create(projectId!, data),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
        queryClient.invalidateQueries({ queryKey: repoMcpKeys.detail(projectId) });
      }
    },
  });

  const syncMutation = useMutation<McpToolSyncResult, ApiError, string>({
    mutationFn: (toolId) => {
      setSyncingId(toolId);
      return toolsApi.sync(projectId!, toolId);
    },
    onSuccess: async () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
        queryClient.invalidateQueries({ queryKey: repoMcpKeys.detail(projectId) });
        // Backend already triggers agent MCP sync; just invalidate agent queries
        queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
      }
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
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
        queryClient.invalidateQueries({ queryKey: repoMcpKeys.detail(projectId) });
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ toolId, confirm }: { toolId: string; confirm?: boolean }) => {
      setDeletingId(toolId);
      return toolsApi.delete(projectId!, toolId, confirm);
    },
    onMutate: async ({ toolId, confirm }: { toolId: string; confirm?: boolean }) => {
      if (!projectId || confirm === false) return;
      const queryKey = toolKeys.list(projectId);
      await queryClient.cancelQueries({ queryKey });
      const snapshot = queryClient.getQueryData<McpToolConfigListResponse>(queryKey);
      if (!snapshot) return;

      queryClient.setQueryData<McpToolConfigListResponse>(queryKey, (old) => {
        if (!old) return old;
        return {
          ...old,
          tools: old.tools.filter((tool) => tool.id !== toolId),
        };
      });
      return { snapshot, queryKey };
    },
    onSuccess: (result) => {
      if (result.success && projectId) {
        queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
        queryClient.invalidateQueries({ queryKey: repoMcpKeys.detail(projectId) });
      }
    },
    onError: (_error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
    },
    onSettled: () => {
      setDeletingId(null);
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
      }
    },
  });

  const authError = query.error instanceof ApiError && query.error.status === 401;

  return {
    tools: query.data?.tools ?? [],
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    rawError: query.error ?? null,
    refetch: query.refetch,

    uploadTool: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error ? formatMutationError(uploadMutation.error, 'upload tool') : null,
    resetUploadError: uploadMutation.reset,

    syncTool: syncMutation.mutateAsync,
    syncingId,
    syncError: syncMutation.error ? formatMutationError(syncMutation.error, 'sync tool') : null,

    updateTool: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error ? formatMutationError(updateMutation.error, 'update tool') : null,
    resetUpdateError: updateMutation.reset,

    deleteTool: deleteMutation.mutateAsync,
    deletingId,
    deleteError: deleteMutation.error ? formatMutationError(deleteMutation.error, 'delete tool') : null,
    deleteResult: deleteMutation.data ?? null,

    authError,
  };
}

export function useUndoableDeleteTool(projectId: string | null | undefined) {
  const { undoableDelete, pendingIds } = useUndoableDelete({
    queryKey: toolKeys.list(projectId ?? ''),
  });

  return {
    deleteTool: (toolId: string, toolName: string) =>
      undoableDelete({
        id: toolId,
        entityLabel: `Tool: ${toolName}`,
        onDelete: () => toolsApi.delete(projectId!, toolId, true).then(() => undefined),
      }),
    pendingIds,
  };
}

export function useToolsListPaginated(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  const result = useInfiniteList<McpToolConfig>({
    queryKey: [...toolKeys.list(projectId ?? ''), 'paginated'],
    queryFn: async (params) => {
      const resp = await toolsApi.listPaginated(projectId!, params);
      return {
        items: resp.tools,
        next_cursor: resp.next_cursor,
        has_more: resp.has_more,
        total_count: resp.total_count,
      } as PaginatedResponse<McpToolConfig>;
    },
    limit: 25,
    staleTime: STALE_TIME_TOOLS,
    enabled: !!projectId,
  });

  return {
    ...result,
    invalidate: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: toolKeys.list(projectId) });
      }
    },
  };
}
