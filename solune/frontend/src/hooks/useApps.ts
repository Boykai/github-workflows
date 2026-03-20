/**
 * TanStack Query hooks for Solune application management.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ApiError, appsApi } from '@/services/api';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { useUndoableDelete } from '@/hooks/useUndoableDelete';
import type {
  App,
  AppAssetInventory,
  AppCreate,
  AppStatusResponse,
  AppUpdate,
  DeleteAppResult,
  Owner,
} from '@/types/apps';

/** Query key factory for apps data. */
export const appKeys = {
  all: ['apps'] as const,
  list: () => [...appKeys.all, 'list'] as const,
  detail: (name: string) => [...appKeys.all, 'detail', name] as const,
  status: (name: string) => [...appKeys.all, 'status', name] as const,
  owners: () => [...appKeys.all, 'owners'] as const,
};

/** Type guard to check if an error is an ApiError. */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

/** Extract a user-friendly message from an error. */
export function getErrorMessage(error: unknown, fallback: string): string {
  if (isApiError(error)) {
    return error.error?.error ?? error.message ?? fallback;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

/** Fetch all applications. */
export function useApps() {
  return useQuery<App[], ApiError>({
    queryKey: appKeys.list(),
    queryFn: () => appsApi.list(),
    staleTime: 30_000,
  });
}

/** Fetch applications with cursor-based pagination. */
export function useAppsPaginated() {
  const queryClient = useQueryClient();
  const result = useInfiniteList<App>({
    queryKey: [...appKeys.list(), 'paginated'],
    queryFn: (params) => appsApi.listPaginated(params),
    limit: 25,
    staleTime: 30_000,
  });

  return {
    ...result,
    invalidate: () => {
      queryClient.invalidateQueries({ queryKey: [...appKeys.list(), 'paginated'] });
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
    },
  };
}

/** Fetch a single application by name. */
export function useApp(name: string | undefined) {
  return useQuery<App, ApiError>({
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
      toast.success('App created');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to create app'), { duration: Infinity });
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
      toast.success('App updated');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to update app'), { duration: Infinity });
    },
  });
}

/** Delete an application. Pass `true` for full asset cleanup. */
export function useDeleteApp() {
  const queryClient = useQueryClient();
  return useMutation<DeleteAppResult | void, ApiError, { appName: string; force?: boolean }>({
    mutationFn: ({ appName, force }) => appsApi.delete(appName, force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
      toast.success('App deleted');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to delete app'), { duration: Infinity });
    },
  });
}

export function useUndoableDeleteApp() {
  const { undoableDelete, pendingIds } = useUndoableDelete({
    queryKey: appKeys.list(),
  });

  return {
    deleteApp: (appName: string, displayName: string, force?: boolean) =>
      undoableDelete({
        id: appName,
        entityLabel: `App: ${displayName}`,
        onDelete: () => appsApi.delete(appName, force).then(() => undefined),
      }),
    pendingIds,
  };
}

/** Fetch the asset inventory for an app (sub-issues, branches, project, repo). */
export function useAppAssets(appName: string | null) {
  return useQuery<AppAssetInventory, ApiError>({
    queryKey: [...appKeys.all, 'assets', appName],
    queryFn: () => appsApi.assets(appName!),
    enabled: !!appName,
    staleTime: 10_000,
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
      toast.success('App started');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to start app'), { duration: Infinity });
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
      toast.success('App stopped');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Failed to stop app'), { duration: Infinity });
    },
  });
}

/** Fetch available repository owners (personal + orgs). */
export function useOwners() {
  return useQuery<Owner[], ApiError>({
    queryKey: appKeys.owners(),
    queryFn: () => appsApi.owners(),
    staleTime: 30_000,
  });
}
