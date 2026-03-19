/**
 * Custom hooks for Chores feature — TanStack React Query.
 *
 * Provides queries for listing chores and mutations for CRUD + trigger + chat.
 */

import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { choresApi, ApiError } from '@/services/api';
import { STALE_TIME_LONG } from '@/constants';
import type {
  Chore,
  ChoreCreate,
  ChoreTemplate,
  ChoreUpdate,
  ChoreTriggerResult,
  ChoreChatMessage,
  ChoreChatResponse,
  ChoreInlineUpdate,
  ChoreInlineUpdateResponse,
  ChoreCreateWithConfirmation,
  ChoreCreateResponse,
} from '@/types';

// ── Query Keys ──

export const choreKeys = {
  all: ['chores'] as const,
  list: (projectId: string) => [...choreKeys.all, 'list', projectId] as const,
  templates: (projectId: string) => [...choreKeys.all, 'templates', projectId] as const,
};

// ── List Hook ──

export function useChoresList(projectId: string | null | undefined) {
  return useQuery<Chore[]>({
    queryKey: choreKeys.list(projectId ?? ''),
    queryFn: () => choresApi.list(projectId!),
    staleTime: STALE_TIME_LONG,
    enabled: !!projectId,
  });
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

// ── Create Mutation ──

export function useCreateChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation<Chore, ApiError, ChoreCreate>({
    mutationFn: (data) => choresApi.create(projectId!, data),
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

// ── Update Mutation ──

export function useUpdateChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation<Chore, ApiError, { choreId: string; data: ChoreUpdate }>({
    mutationFn: ({ choreId, data }) => choresApi.update(projectId!, choreId, data),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
      toast.success('Chore updated');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update chore', { duration: Infinity });
    },
  });
}

// ── Delete Mutation ──

export function useDeleteChore(projectId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation<{ deleted: boolean; closed_issue_number: number | null }, ApiError, string>({
    mutationFn: (choreId) => choresApi.delete(projectId!, choreId),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
      toast.success('Chore deleted');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete chore', { duration: Infinity });
    },
  });
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

  return useMutation<
    ChoreInlineUpdateResponse,
    ApiError,
    { choreId: string; data: ChoreInlineUpdate }
  >({
    mutationFn: ({ choreId, data }) => choresApi.inlineUpdate(projectId!, choreId, data),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
      toast.success('Chore updated');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update chore', { duration: Infinity });
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
