import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import type { PaginatedResponse } from '@/types';
import { useInfiniteList } from './useInfiniteList';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
  return { queryClient, wrapper };
}

interface TestItem {
  id: string;
  name: string;
}

function makePage(
  items: TestItem[],
  opts: { has_more?: boolean; next_cursor?: string | null; total_count?: number | null } = {},
): PaginatedResponse<TestItem> {
  return {
    items,
    has_more: opts.has_more ?? false,
    next_cursor: opts.next_cursor ?? null,
    total_count: opts.total_count ?? items.length,
  };
}

describe('useInfiniteList', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetches the first page and exposes allItems', async () => {
    const page = makePage([{ id: '1', name: 'Alpha' }], { total_count: 1 });
    const queryFn = vi.fn().mockResolvedValue(page);
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useInfiniteList<TestItem>({
          queryKey: ['test', 'items'],
          queryFn,
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.allItems).toEqual([{ id: '1', name: 'Alpha' }]);
    expect(result.current.totalCount).toBe(1);
    expect(queryFn).toHaveBeenCalledWith({ limit: 25, cursor: undefined });
  });

  it('flattens items from multiple pages', async () => {
    const page1 = makePage([{ id: '1', name: 'Alpha' }], {
      has_more: true,
      next_cursor: 'cursor-1',
      total_count: 2,
    });
    const page2 = makePage([{ id: '2', name: 'Beta' }], { total_count: 2 });
    const queryFn = vi.fn()
      .mockResolvedValueOnce(page1)
      .mockResolvedValueOnce(page2);

    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useInfiniteList<TestItem>({
          queryKey: ['test', 'multi'],
          queryFn,
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Fetch next page
    await act(async () => {
      await result.current.fetchNextPage();
    });

    await waitFor(() => expect(result.current.allItems).toHaveLength(2));

    expect(result.current.allItems).toEqual([
      { id: '1', name: 'Alpha' },
      { id: '2', name: 'Beta' },
    ]);
    expect(result.current.totalCount).toBe(2);
    expect(queryFn).toHaveBeenCalledTimes(2);
    expect(queryFn).toHaveBeenLastCalledWith({ limit: 25, cursor: 'cursor-1' });
  });

  it('does not fetch when enabled is false', () => {
    const queryFn = vi.fn();
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useInfiniteList<TestItem>({
          queryKey: ['test', 'disabled'],
          queryFn,
          enabled: false,
        }),
      { wrapper },
    );

    expect(queryFn).not.toHaveBeenCalled();
    expect(result.current.allItems).toEqual([]);
    expect(result.current.totalCount).toBeNull();
  });

  it('uses default limit of 25', async () => {
    const page = makePage([{ id: '1', name: 'Alpha' }]);
    const queryFn = vi.fn().mockResolvedValue(page);
    const { wrapper } = createWrapper();

    renderHook(
      () =>
        useInfiniteList<TestItem>({
          queryKey: ['test', 'default-limit'],
          queryFn,
        }),
      { wrapper },
    );

    await waitFor(() => expect(queryFn).toHaveBeenCalled());
    expect(queryFn).toHaveBeenCalledWith({ limit: 25, cursor: undefined });
  });

  it('uses custom limit when specified', async () => {
    const page = makePage([{ id: '1', name: 'Alpha' }]);
    const queryFn = vi.fn().mockResolvedValue(page);
    const { wrapper } = createWrapper();

    renderHook(
      () =>
        useInfiniteList<TestItem>({
          queryKey: ['test', 'custom-limit'],
          queryFn,
          limit: 50,
        }),
      { wrapper },
    );

    await waitFor(() => expect(queryFn).toHaveBeenCalled());
    expect(queryFn).toHaveBeenCalledWith({ limit: 50, cursor: undefined });
  });

  it('resetPagination resets queries', async () => {
    const page = makePage([{ id: '1', name: 'Alpha' }]);
    const queryFn = vi.fn().mockResolvedValue(page);
    const { queryClient, wrapper } = createWrapper();
    const resetSpy = vi.spyOn(queryClient, 'resetQueries');

    const { result } = renderHook(
      () =>
        useInfiniteList<TestItem>({
          queryKey: ['test', 'reset'],
          queryFn,
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    act(() => {
      result.current.resetPagination();
    });

    expect(resetSpy).toHaveBeenCalledWith({ queryKey: ['test', 'reset'] });
  });

  it('does not expose hasNextPage when last page has_more is false', async () => {
    const page = makePage([{ id: '1', name: 'Alpha' }], { has_more: false });
    const queryFn = vi.fn().mockResolvedValue(page);
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useInfiniteList<TestItem>({
          queryKey: ['test', 'no-next'],
          queryFn,
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.hasNextPage).toBe(false);
  });
});
