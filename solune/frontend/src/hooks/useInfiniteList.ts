/**
 * useInfiniteList — shared wrapper around TanStack Query's useInfiniteQuery
 * for cursor-based paginated list endpoints.
 */

import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import type { PaginatedResponse } from '@/types';

export interface UseInfiniteListOptions<T> {
  queryKey: readonly unknown[];
  queryFn: (params: { limit: number; cursor?: string }) => Promise<PaginatedResponse<T>>;
  limit?: number;
  enabled?: boolean;
  staleTime?: number;
}

export function useInfiniteList<T>(options: UseInfiniteListOptions<T>) {
  const { queryKey, queryFn, limit = 25, enabled = true, staleTime } = options;
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) =>
      queryFn({ limit, cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? (lastPage.next_cursor ?? undefined) : undefined,
    enabled,
    staleTime,
  });

  const allItems = useMemo(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data?.pages],
  );

  const totalCount = query.data?.pages[0]?.total_count ?? null;

  const resetPagination = useCallback(() => {
    queryClient.resetQueries({ queryKey });
  }, [queryClient, queryKey]);

  return {
    ...query,
    allItems,
    totalCount,
    resetPagination,
  };
}
