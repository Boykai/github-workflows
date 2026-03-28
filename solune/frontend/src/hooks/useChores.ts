/**
 * Custom hooks for Chores feature — TanStack React Query.
 *
 * Provides queries for listing chores and mutations for CRUD + trigger + chat.
 */

import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { toast } from 'sonner';
import { choresApi, ApiError } from '@/services/api';
import { STALE_TIME_LONG } from '@/constants';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { useUndoableDelete } from '@/hooks/useUndoableDelete';
import type {
  Chore,
  ChoreCreate,
  ChoreTemplate,
  ChoreUpdate,
  ChoreStatus,
  ChoreTriggerResult,
  ChoreChatMessage,
  ChoreChatResponse,
  ChoreInlineUpdate,
  ChoreCreateWithConfirmation,
  ChoreCreateResponse,
  PaginatedResponse,
  ScheduleType,
} from '@/types';

// ── Query Keys ──

export const choreKeys = {
  all: ['chores'] as const,
  list: (projectId: string) => [...choreKeys.all, 'list', projectId] as const,
  names: (projectId: string) => [...choreKeys.all, 'names', projectId] as const,
  templates: (projectId: string) => [...choreKeys.all, 'templates', projectId] as const,
};

// ── Filter Params Interface ──

export interface ChoresFilterParams {
  status?: ChoreStatus;
  scheduleType?: ScheduleType | 'unscheduled';
  search?: string;
  sort?: 'name' | 'updated_at' | 'created_at' | 'attention';
  order?: 'asc' | 'desc';
}

// ── Paginated List Hook ──

export function useChoresListPaginated(
  projectId: string | null | undefined,
  filters?: ChoresFilterParams,
) {
  const queryClient = useQueryClient();
  const result = useInfiniteList<Chore>({
    queryKey: [...choreKeys.list(projectId ?? ''), 'paginated', filters ?? {}],
    queryFn: (params) =>
      choresApi.listPaginated(projectId!, { ...params, ...filters }),
    limit: 25,
    staleTime: STALE_TIME_LONG,
    enabled: !!projectId,
  });

  return {
    ...result,
    invalidate: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
    },
  };
}

// ── Templates Hook ──

export function useChoreTemplates(projectId: string | null | undefined) {
  return useQuery<ChoreTemplate[]>({
    queryKey: choreKeys.templates(projectId ?? ''),
    queryFn: () => choresApi.listTemplates(projectId!),
    staleTime: STALE_TIME_LONG,
    enabled: !!projectId,
  });
}

// ── All Chore Names Hook (unpaginated, for membership checks) ──

/**
 * Fetch ALL chore names for a project via the lightweight `/chore-names`
 * endpoint.  Returns a complete, unfiltered list of names suitable for
 * set-membership checks (e.g. determining which templates are already
 * created).  Uses a 60-second stale time to balance freshness and traffic.
 */
export function useAllChoreNames(projectId: string | null | undefined) {
  return useQuery<string[]>({
    queryKey: choreKeys.names(projectId ?? ''),
    queryFn: () => choresApi.listChoreNames(projectId!),
    staleTime: 60_000,
    enabled: !!projectId,
  });
}

// ── Create Mutation ──

export function useCreateChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ChoreCreate) => choresApi.create(projectId!, data),
    onMutate: async (data: ChoreCreate) => {
      if (!projectId) return;
      const queryKey = choreKeys.list(projectId);
      const paginatedQueryKey = [...choreKeys.list(projectId), 'paginated'];
      await queryClient.cancelQueries({ queryKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const snapshot = queryClient.getQueryData<Chore[]>(queryKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey);
      if (!snapshot) return;

      const now = new Date().toISOString();
      const placeholder = {
        id: `temp-${Date.now()}`,
        project_id: projectId,
        name: data.name,
        template_path: '',
        template_content: data.template_content ?? '',
        schedule_type: null,
        schedule_value: null,
        status: 'active' as const,
        last_triggered_at: null,
        last_triggered_count: 0,
        current_issue_number: null,
        current_issue_node_id: null,
        pr_number: null,
        pr_url: null,
        tracking_issue_number: null,
        execution_count: 0,
        ai_enhance_enabled: false,
        agent_pipeline_id: '',
        is_preset: false,
        preset_id: '',
        created_at: now,
        updated_at: now,
        _optimistic: true,
      } satisfies Chore & { _optimistic: boolean };

      queryClient.setQueryData<Chore[]>(queryKey, [placeholder, ...snapshot]);

      if (paginatedSnapshot?.pages?.length) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page, index) =>
            index === 0
              ? { ...page, items: [placeholder, ...page.items] }
              : page
          ),
        });
      }

      return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: () => {
      toast.success('Chore created');
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(error.message || 'Failed to create chore', { duration: Infinity });
    },
    onSettled: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
    },
  });
}

// ── Update Mutation ──

export function useUpdateChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ choreId, data }: { choreId: string; data: ChoreUpdate }) =>
      choresApi.update(projectId!, choreId, data),
    onMutate: async ({ choreId, data }: { choreId: string; data: ChoreUpdate }) => {
      if (!projectId) return;
      const queryKey = choreKeys.list(projectId);
      const paginatedQueryKey = [...choreKeys.list(projectId), 'paginated'];
      await queryClient.cancelQueries({ queryKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const snapshot = queryClient.getQueryData<Chore[]>(queryKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey);
      if (!snapshot) return;

      queryClient.setQueryData<Chore[]>(queryKey, (old) =>
        old?.map((chore) =>
          chore.id === choreId ? { ...chore, ...data, updated_at: new Date().toISOString() } : chore,
        ),
      );

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.map((item) =>
              item.id === choreId ? { ...item, ...data, updated_at: new Date().toISOString() } : item,
            ),
          })),
        });
      }

      return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: () => {
      toast.success('Chore updated');
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(error.message || 'Failed to update chore', { duration: Infinity });
    },
    onSettled: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
    },
  });
}

// ── Delete Mutation ──

export function useDeleteChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (choreId: string) => choresApi.delete(projectId!, choreId),
    onMutate: async (choreId: string) => {
      if (!projectId) return;
      const queryKey = choreKeys.list(projectId);
      const paginatedQueryKey = [...choreKeys.list(projectId), 'paginated'];
      await queryClient.cancelQueries({ queryKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const snapshot = queryClient.getQueryData<Chore[]>(queryKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey);
      if (!snapshot) return;

      queryClient.setQueryData<Chore[]>(queryKey, (old) =>
        old?.filter((chore) => chore.id !== choreId),
      );

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.filter((item) => item.id !== choreId),
          })),
        });
      }

      return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: () => {
      toast.success('Chore deleted');
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(error.message || 'Failed to delete chore', { duration: Infinity });
    },
    onSettled: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
    },
  });
}

// ── Undoable Delete ──

export function useUndoableDeleteChore(projectId: string | null | undefined) {
  const { undoableDelete, pendingIds } = useUndoableDelete({
    queryKey: choreKeys.list(projectId ?? ''),
  });

  return {
    deleteChore: (choreId: string, choreName: string) =>
      undoableDelete({
        id: choreId,
        entityLabel: `Chore: ${choreName}`,
        onDelete: () => choresApi.delete(projectId!, choreId).then(() => undefined),
      }),
    pendingIds,
  };
}

// ── Trigger Mutation ──

export function useTriggerChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation<ChoreTriggerResult, ApiError, { choreId: string; parentIssueCount?: number }>({
    mutationFn: ({ choreId, parentIssueCount }) =>
      choresApi.trigger(projectId!, choreId, parentIssueCount),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
      toast.success('Chore triggered');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to trigger chore', { duration: Infinity });
    },
  });
}

// ── Evaluate Triggers Polling ──

/**
 * Poll the evaluate-triggers endpoint every 60 s while the Chores page is mounted.
 * Automatically invalidates the chores list when at least one chore is triggered.
 * Only starts polling once `boardLoaded` is true (i.e. boardData has columns).
 */
export function useEvaluateChoresTriggers(
  projectId: string | null | undefined,
  parentIssueCount: number,
  boardLoaded: boolean
) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!projectId || !boardLoaded) return;

    const run = () => {
      choresApi
        .evaluateTriggers(projectId, parentIssueCount)
        .then(({ triggered }) => {
          if (triggered > 0 && projectId) {
            queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
          }
        })
        .catch(() => {
          // Polling failures are non-critical; silent ignore
        });
    };

    run(); // immediate first run now that board data is ready
    const id = window.setInterval(run, 60_000);
    return () => window.clearInterval(id);
  }, [projectId, parentIssueCount, boardLoaded, queryClient]);
}

// ── Chat Mutation ──

export function useChoreChat(projectId: string | null | undefined) {
  return useMutation<ChoreChatResponse, ApiError, ChoreChatMessage>({
    mutationFn: (data) => choresApi.chat(projectId!, data),
  });
}

// ── Inline Update Mutation ──

export function useInlineUpdateChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ choreId, data }: { choreId: string; data: ChoreInlineUpdate }) =>
      choresApi.inlineUpdate(projectId!, choreId, data),
    onMutate: async ({ choreId, data }: { choreId: string; data: ChoreInlineUpdate }) => {
      if (!projectId) return;
      const queryKey = choreKeys.list(projectId);
      const paginatedQueryKey = [...choreKeys.list(projectId), 'paginated'];
      await queryClient.cancelQueries({ queryKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const snapshot = queryClient.getQueryData<Chore[]>(queryKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey);
      if (!snapshot) return;

      queryClient.setQueryData<Chore[]>(queryKey, (old) =>
        old?.map((chore) =>
          chore.id === choreId ? { ...chore, ...data, updated_at: new Date().toISOString() } : chore,
        ),
      );

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<Chore>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.map((item) =>
              item.id === choreId ? { ...item, ...data, updated_at: new Date().toISOString() } : item,
            ),
          })),
        });
      }

      return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: () => {
      toast.success('Chore updated');
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(error.message || 'Failed to update chore', { duration: Infinity });
    },
    onSettled: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
    },
  });
}

// ── Create with Auto-Merge Mutation ──

export function useCreateChoreWithAutoMerge(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation<ChoreCreateResponse, ApiError, ChoreCreateWithConfirmation>({
    mutationFn: (data) => choresApi.createWithAutoMerge(projectId!, data),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
      toast.success('Chore created');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create chore', { duration: Infinity });
    },
  });
}
