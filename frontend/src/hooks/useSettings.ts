/**
 * Custom hook for managing settings state via TanStack Query.
 *
 * Provides queries for user, global, and project settings,
 * plus mutations with optimistic updates and cache invalidation.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '@/services/api';
import type {
  EffectiveUserSettings,
  UserPreferencesUpdate,
  GlobalSettings,
  GlobalSettingsUpdate,
  EffectiveProjectSettings,
  ProjectSettingsUpdate,
} from '@/types';

// ── Query Keys ──

export const settingsKeys = {
  all: ['settings'] as const,
  user: () => [...settingsKeys.all, 'user'] as const,
  global: () => [...settingsKeys.all, 'global'] as const,
  project: (projectId: string) => [...settingsKeys.all, 'project', projectId] as const,
};

// ── User Settings ──

export function useUserSettings() {
  const queryClient = useQueryClient();

  const query = useQuery<EffectiveUserSettings>({
    queryKey: settingsKeys.user(),
    queryFn: settingsApi.getUserSettings,
    staleTime: 5 * 60 * 1000, // 5 min
  });

  const mutation = useMutation({
    mutationFn: (update: UserPreferencesUpdate) =>
      settingsApi.updateUserSettings(update),
    onSuccess: (data) => {
      queryClient.setQueryData(settingsKeys.user(), data);
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateSettings: mutation.mutateAsync,
    isUpdating: mutation.isPending,
  };
}

// ── Global Settings ──

export function useGlobalSettings() {
  const queryClient = useQueryClient();

  const query = useQuery<GlobalSettings>({
    queryKey: settingsKeys.global(),
    queryFn: settingsApi.getGlobalSettings,
    staleTime: 5 * 60 * 1000,
  });

  const mutation = useMutation({
    mutationFn: (update: GlobalSettingsUpdate) =>
      settingsApi.updateGlobalSettings(update),
    onSuccess: (data) => {
      queryClient.setQueryData(settingsKeys.global(), data);
      // User effective settings may have changed if global defaults changed
      queryClient.invalidateQueries({ queryKey: settingsKeys.user() });
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateSettings: mutation.mutateAsync,
    isUpdating: mutation.isPending,
  };
}

// ── Project Settings ──

export function useProjectSettings(projectId: string | undefined) {
  const queryClient = useQueryClient();

  const query = useQuery<EffectiveProjectSettings>({
    queryKey: settingsKeys.project(projectId ?? ''),
    queryFn: () => settingsApi.getProjectSettings(projectId!),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000,
  });

  const mutation = useMutation({
    mutationFn: (update: ProjectSettingsUpdate) =>
      settingsApi.updateProjectSettings(projectId!, update),
    onSuccess: (data) => {
      queryClient.setQueryData(settingsKeys.project(projectId ?? ''), data);
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateSettings: mutation.mutateAsync,
    isUpdating: mutation.isPending,
  };
}
