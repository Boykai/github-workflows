import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useUndoableDelete } from './useUndoableDelete';

const sonnerMocks = vi.hoisted(() => {
  const toast = vi.fn();
  return {
    toast: Object.assign(toast, {
      dismiss: vi.fn(),
      error: vi.fn(),
      success: vi.fn(),
    }),
  };
});

vi.mock('sonner', () => ({
  toast: sonnerMocks.toast,
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
  return { queryClient, wrapper };
}

describe('useUndoableDelete', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('preserves the original snapshots across duplicate pending deletes and restores all list shapes on undo', async () => {
    const { queryClient, wrapper } = createWrapper();
    const listKey = ['tools', 'list', 'proj-1'];
    const paginatedKey = [...listKey, 'paginated'];
    const listSnapshot = {
      tools: [
        { id: 'tool-1', name: 'My Tool' },
        { id: 'tool-2', name: 'Other Tool' },
      ],
    };
    const paginatedSnapshot = {
      pages: [
        {
          items: [
            { id: 'tool-1', name: 'My Tool' },
            { id: 'tool-2', name: 'Other Tool' },
          ],
          next_cursor: null,
          has_more: false,
          total_count: 2,
        },
      ],
      pageParams: [undefined],
    };
    queryClient.setQueryData(listKey, listSnapshot);
    queryClient.setQueryData(paginatedKey, paginatedSnapshot);

    const { result } = renderHook(
      () =>
        useUndoableDelete({
          queryKeys: [listKey, paginatedKey],
          undoTimeoutMs: 5000,
        }),
      { wrapper },
    );

    act(() => {
      result.current.undoableDelete({
        id: 'tool-1',
        entityLabel: 'Tool: My Tool',
        onDelete: vi.fn().mockResolvedValue(undefined),
      });
      result.current.undoableDelete({
        id: 'tool-1',
        entityLabel: 'Tool: My Tool',
        onDelete: vi.fn().mockResolvedValue(undefined),
      });
    });

    expect(queryClient.getQueryData(listKey)).toEqual({
      tools: [{ id: 'tool-2', name: 'Other Tool' }],
    });
    expect(queryClient.getQueryData(paginatedKey)).toEqual({
      pages: [
        {
          items: [{ id: 'tool-2', name: 'Other Tool' }],
          next_cursor: null,
          has_more: false,
          total_count: 2,
        },
      ],
      pageParams: [undefined],
    });

    const lastToastCall = sonnerMocks.toast.mock.calls.at(-1);
    const action = lastToastCall?.[1]?.action;

    act(() => {
      action?.onClick?.();
    });

    await waitFor(() => {
      expect(queryClient.getQueryData(listKey)).toEqual(listSnapshot);
      expect(queryClient.getQueryData(paginatedKey)).toEqual(paginatedSnapshot);
    });
  });

  it('keeps pending deletes alive across unmount when restoreOnUnmount is false', async () => {
    vi.useFakeTimers();
    const { queryClient, wrapper } = createWrapper();
    const listKey = ['apps', 'list'];
    const onDelete = vi.fn().mockResolvedValue(undefined);
    queryClient.setQueryData(listKey, [{ name: 'demo-app', display_name: 'Demo App' }]);

    const { result, unmount } = renderHook(
      () =>
        useUndoableDelete({
          queryKey: listKey,
          undoTimeoutMs: 1000,
          restoreOnUnmount: false,
        }),
      { wrapper },
    );

    act(() => {
      result.current.undoableDelete({
        id: 'demo-app',
        entityLabel: 'App: Demo App',
        onDelete,
      });
    });

    expect(queryClient.getQueryData(listKey)).toEqual([]);

    unmount();

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(onDelete).toHaveBeenCalledOnce();
    expect(queryClient.getQueryData(listKey)).toEqual([]);
  });
});
