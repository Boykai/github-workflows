/**
 * Custom hook for managing settings state via TanStack Query.
 *
 * Provides queries for user, global, and project settings,
 * plus mutations with optimistic updates and cache invalidation.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi, signalApi } from '@/services/api';
import { STALE_TIME_LONG, STALE_TIME_SHORT } from '@/constants';
import type {
  EffectiveUserSettings,
  UserPreferencesUpdate,
  GlobalSettings,
  GlobalSettingsUpdate,
  EffectiveProjectSettings,
  ProjectSettingsUpdate,
  SignalConnection,
  SignalLinkResponse,
  SignalLinkStatusResponse,
  SignalPreferences,
  SignalPreferencesUpdate,
  SignalBannersResponse,
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
    staleTime: STALE_TIME_LONG,
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
    staleTime: STALE_TIME_LONG,
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
    staleTime: STALE_TIME_LONG,
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

// ── Signal Connection Hooks ──

export const signalKeys = {
  all: ['signal'] as const,
  connection: () => [...signalKeys.all, 'connection'] as const,
  linkStatus: () => [...signalKeys.all, 'linkStatus'] as const,
  preferences: () => [...signalKeys.all, 'preferences'] as const,
  banners: () => [...signalKeys.all, 'banners'] as const,
};

/** Fetch Signal connection status. */
export function useSignalConnection() {
  const query = useQuery<SignalConnection>({
    queryKey: signalKeys.connection(),
    queryFn: signalApi.getConnection,
    staleTime: STALE_TIME_LONG,
  });

  return {
    connection: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

/** Initiate Signal QR code linking. */
export function useInitiateSignalLink() {
  const queryClient = useQueryClient();

  const mutation = useMutation<SignalLinkResponse, Error, string | undefined>({
    mutationFn: (deviceName?: string) => signalApi.initiateLink(deviceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: signalKeys.connection() });
    },
  });

  return {
    initiateLink: mutation.mutateAsync,
    data: mutation.data,
    isPending: mutation.isPending,
    error: mutation.error,
    reset: mutation.reset,
  };
}

/** Poll Signal link status (enabled when linking is in progress). */
export function useSignalLinkStatus(enabled: boolean) {
  const queryClient = useQueryClient();

  const query = useQuery<SignalLinkStatusResponse>({
    queryKey: signalKeys.linkStatus(),
    queryFn: signalApi.checkLinkStatus,
    enabled,
    refetchInterval: enabled ? 2000 : false,
    staleTime: STALE_TIME_SHORT,
  });

  // When link completes, invalidate connection query
  const status = query.data?.status;
  if (status === 'connected') {
    queryClient.invalidateQueries({ queryKey: signalKeys.connection() });
  }

  return {
    linkStatus: query.data,
    isPolling: query.isFetching,
  };
}

/** Disconnect Signal account. */
export function useDisconnectSignal() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => signalApi.disconnect(),
    onSuccess: () => {
      queryClient.setQueryData(signalKeys.connection(), null);
      queryClient.invalidateQueries({ queryKey: signalKeys.connection() });
      queryClient.invalidateQueries({ queryKey: signalKeys.preferences() });
    },
  });

  return {
    disconnect: mutation.mutateAsync,
    isPending: mutation.isPending,
    error: mutation.error,
  };
}

/** Fetch Signal notification preferences. */
export function useSignalPreferences() {
  const query = useQuery<SignalPreferences>({
    queryKey: signalKeys.preferences(),
    queryFn: signalApi.getPreferences,
    staleTime: STALE_TIME_LONG,
  });

  return {
    preferences: query.data,
    isLoading: query.isLoading,
    error: query.error,
  };
}

/** Update Signal notification preferences. */
export function useUpdateSignalPreferences() {
  const queryClient = useQueryClient();

  const mutation = useMutation<SignalPreferences, Error, SignalPreferencesUpdate>({
    mutationFn: (data) => signalApi.updatePreferences(data),
    onSuccess: (data) => {
      queryClient.setQueryData(signalKeys.preferences(), data);
    },
  });

  return {
    updatePreferences: mutation.mutateAsync,
    isPending: mutation.isPending,
    error: mutation.error,
  };
}

/** Fetch active Signal conflict banners. */
export function useSignalBanners() {
  const query = useQuery<SignalBannersResponse>({
    queryKey: signalKeys.banners(),
    queryFn: signalApi.getBanners,
    staleTime: STALE_TIME_SHORT,
  });

  return {
    banners: query.data?.banners ?? [],
    isLoading: query.isLoading,
    error: query.error,
  };
}

/** Dismiss a conflict banner. */
export function useDismissBanner() {
  const queryClient = useQueryClient();

  const mutation = useMutation<{ message: string }, Error, string>({
    mutationFn: (bannerId) => signalApi.dismissBanner(bannerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: signalKeys.banners() });
    },
  });

  return {
    dismissBanner: mutation.mutateAsync,
    isPending: mutation.isPending,
  };
}
