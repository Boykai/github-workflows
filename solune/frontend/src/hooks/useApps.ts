/**
 * TanStack Query hooks for Solune application management.
 */

import { useMutation, useQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ApiError, appsApi } from '@/services/api';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { useUndoableDelete } from '@/hooks/useUndoableDelete';
import type {
  App,
  AppAssetInventory,
  AppCreate,
  AppUpdate,
  Owner,
} from '@/types/apps';
import type { PaginatedResponse } from '@/types';

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

  return useMutation({
    mutationFn: (data: AppCreate) => appsApi.create(data),
    onMutate: async (data: AppCreate) => {
      const queryKey = appKeys.list();
      const paginatedQueryKey = [...appKeys.list(), 'paginated'];
      await queryClient.cancelQueries({ queryKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const snapshot = queryClient.getQueryData<App[]>(queryKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey);
      if (!snapshot) return;

      const now = new Date().toISOString();
      const placeholder = {
        name: data.name || `temp-${Date.now()}`,
        display_name: data.display_name || data.name || '',
        description: data.description || '',
        directory_path: '',
        associated_pipeline_id: null,
        status: 'creating' as const,
        repo_type: (data.repo_type ?? 'new-repo') as App['repo_type'],
        external_repo_url: null,
        github_repo_url: null,
        github_project_url: null,
        github_project_id: null,
        parent_issue_number: null,
        parent_issue_url: null,
        port: null,
        error_message: null,
        created_at: now,
        updated_at: now,
        warnings: null,
        _optimistic: true,
      } satisfies App & { _optimistic: boolean };

      queryClient.setQueryData<App[]>(queryKey, [placeholder, ...snapshot]);

      if (paginatedSnapshot?.pages?.length) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey, {
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
      toast.success('App created');
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(getErrorMessage(error, 'Failed to create app'), { duration: Infinity });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
    },
  });
}

/** Update an existing application. */
export function useUpdateApp(name: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AppUpdate) => appsApi.update(name, data),
    onMutate: async (data: AppUpdate) => {
      const listKey = appKeys.list();
      const detailKey = appKeys.detail(name);
      const paginatedQueryKey = [...appKeys.list(), 'paginated'];
      await queryClient.cancelQueries({ queryKey: listKey });
      await queryClient.cancelQueries({ queryKey: detailKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const listSnapshot = queryClient.getQueryData<App[]>(listKey);
      const detailSnapshot = queryClient.getQueryData<App>(detailKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey);

      if (listSnapshot) {
        queryClient.setQueryData<App[]>(listKey, (old) =>
          old?.map((app) =>
            app.name === name ? { ...app, ...data, updated_at: new Date().toISOString() } : app,
          ),
        );
      }
      if (detailSnapshot) {
        queryClient.setQueryData<App>(detailKey, (old) =>
          old ? { ...old, ...data, updated_at: new Date().toISOString() } : old,
        );
      }

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.map((item) =>
              item.name === name ? { ...item, ...data, updated_at: new Date().toISOString() } : item,
            ),
          })),
        });
      }

      return { listSnapshot, detailSnapshot, listKey, detailKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: () => {
      toast.success('App updated');
    },
    onError: (error, _variables, context) => {
      if (context?.listSnapshot) {
        queryClient.setQueryData(context.listKey, context.listSnapshot);
      }
      if (context?.detailSnapshot) {
        queryClient.setQueryData(context.detailKey, context.detailSnapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(getErrorMessage(error, 'Failed to update app'), { duration: Infinity });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
      queryClient.invalidateQueries({ queryKey: appKeys.detail(name) });
    },
  });
}

/** Delete an application. Pass `true` for full asset cleanup. */
export function useDeleteApp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ appName, force }: { appName: string; force?: boolean }) => appsApi.delete(appName, force),
    onMutate: async ({ appName }: { appName: string; force?: boolean }) => {
      const queryKey = appKeys.list();
      const paginatedQueryKey = [...appKeys.list(), 'paginated'];
      await queryClient.cancelQueries({ queryKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const snapshot = queryClient.getQueryData<App[]>(queryKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey);
      if (!snapshot) return;

      queryClient.setQueryData<App[]>(queryKey, (old) =>
        old?.filter((app) => app.name !== appName),
      );

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.filter((item) => item.name !== appName),
          })),
        });
      }

      return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: () => {
      toast.success('App deleted');
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(getErrorMessage(error, 'Failed to delete app'), { duration: Infinity });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
    },
  });
}

export function useUndoableDeleteApp() {
  const { undoableDelete, pendingIds } = useUndoableDelete({
    queryKeys: [appKeys.list(), [...appKeys.list(), 'paginated']],
    restoreOnUnmount: false,
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

  return useMutation({
    mutationFn: (appName: string) => appsApi.start(appName),
    onMutate: async (appName: string) => {
      const listKey = appKeys.list();
      const detailKey = appKeys.detail(appName);
      const paginatedQueryKey = [...appKeys.list(), 'paginated'];
      await queryClient.cancelQueries({ queryKey: listKey });
      await queryClient.cancelQueries({ queryKey: detailKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const listSnapshot = queryClient.getQueryData<App[]>(listKey);
      const detailSnapshot = queryClient.getQueryData<App>(detailKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey);

      if (listSnapshot) {
        queryClient.setQueryData<App[]>(listKey, (old) =>
          old?.map((app) =>
            app.name === appName ? { ...app, status: 'active' as const } : app,
          ),
        );
      }
      if (detailSnapshot) {
        queryClient.setQueryData<App>(detailKey, (old) =>
          old ? { ...old, status: 'active' as const } : old,
        );
      }

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.map((item) =>
              item.name === appName ? { ...item, status: 'active' as const } : item,
            ),
          })),
        });
      }

      return { listSnapshot, detailSnapshot, listKey, detailKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: (_data, appName) => {
      toast.success('App started');
      queryClient.invalidateQueries({ queryKey: appKeys.detail(appName) });
    },
    onError: (error, _variables, context) => {
      if (context?.listSnapshot) {
        queryClient.setQueryData(context.listKey, context.listSnapshot);
      }
      if (context?.detailSnapshot) {
        queryClient.setQueryData(context.detailKey, context.detailSnapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(getErrorMessage(error, 'Failed to start app'), { duration: Infinity });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
    },
  });
}

/** Stop an application. */
export function useStopApp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (appName: string) => appsApi.stop(appName),
    onMutate: async (appName: string) => {
      const listKey = appKeys.list();
      const detailKey = appKeys.detail(appName);
      const paginatedQueryKey = [...appKeys.list(), 'paginated'];
      await queryClient.cancelQueries({ queryKey: listKey });
      await queryClient.cancelQueries({ queryKey: detailKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const listSnapshot = queryClient.getQueryData<App[]>(listKey);
      const detailSnapshot = queryClient.getQueryData<App>(detailKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey);

      if (listSnapshot) {
        queryClient.setQueryData<App[]>(listKey, (old) =>
          old?.map((app) =>
            app.name === appName ? { ...app, status: 'stopped' as const } : app,
          ),
        );
      }
      if (detailSnapshot) {
        queryClient.setQueryData<App>(detailKey, (old) =>
          old ? { ...old, status: 'stopped' as const } : old,
        );
      }

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<App>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.map((item) =>
              item.name === appName ? { ...item, status: 'stopped' as const } : item,
            ),
          })),
        });
      }

      return { listSnapshot, detailSnapshot, listKey, detailKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: (_data, appName) => {
      toast.success('App stopped');
      queryClient.invalidateQueries({ queryKey: appKeys.detail(appName) });
    },
    onError: (error, _variables, context) => {
      if (context?.listSnapshot) {
        queryClient.setQueryData(context.listKey, context.listSnapshot);
      }
      if (context?.detailSnapshot) {
        queryClient.setQueryData(context.detailKey, context.detailSnapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(getErrorMessage(error, 'Failed to stop app'), { duration: Infinity });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: appKeys.list() });
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
