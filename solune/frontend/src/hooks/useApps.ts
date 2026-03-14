/**
 * TanStack Query hooks for Solune application management.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { appsApi, type ApiError } from '@/services/api';
import type { App, AppCreate, AppStatusResponse, AppUpdate } from '@/types/apps';

/** Query key factory for apps data. */
export const appKeys = {
  all: ['apps'] as const,
  list: () => [...appKeys.all, 'list'] as const,
  detail: (name: string) => [...appKeys.all, 'detail', name] as const,
  status: (name: string) => [...appKeys.all, 'status', name] as const,
};

/** Fetch all applications. */
export function useApps() {
  return useQuery<App[]>({
    queryKey: appKeys.list(),
    queryFn: () => appsApi.list(),
    staleTime: 30_000,
  });
}

/** Fetch a single application by name. */
export function useApp(name: string | undefined) {
  return useQuery<App>({
    queryKey: appKeys.detail(name ?? ''),
    queryFn: () => appsApi.get(name!),
    enabled: !!name,
    staleTime: 30_000,
  });
}

/** Create a new application. */
export function useCreateApp() {
  const queryClient = useQueryClient();
  return useMutation<App, ApiError, AppCreate>({
    mutationFn: (data) => appsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
    },
  });
}

/** Update an existing application. */
export function useUpdateApp(name: string) {
  const queryClient = useQueryClient();
  return useMutation<App, ApiError, AppUpdate>({
    mutationFn: (data) => appsApi.update(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
      queryClient.invalidateQueries({ queryKey: appKeys.detail(name) });
    },
  });
}

/** Delete an application. */
export function useDeleteApp() {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (appName) => appsApi.delete(appName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
    },
  });
}

/** Start an application. */
export function useStartApp() {
  const queryClient = useQueryClient();
  return useMutation<AppStatusResponse, ApiError, string>({
    mutationFn: (appName) => appsApi.start(appName),
    onSuccess: (_data, appName) => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
      queryClient.invalidateQueries({ queryKey: appKeys.detail(appName) });
    },
  });
}

/** Stop an application. */
export function useStopApp() {
  const queryClient = useQueryClient();
  return useMutation<AppStatusResponse, ApiError, string>({
    mutationFn: (appName) => appsApi.stop(appName),
    onSuccess: (_data, appName) => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
      queryClient.invalidateQueries({ queryKey: appKeys.detail(appName) });
    },
  });
}
