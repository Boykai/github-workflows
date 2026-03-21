import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

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

vi.mock('@/services/api', () => ({
  toolsApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    sync: vi.fn(),
    delete: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, error: { error: string }) {
      super(error.error);
      this.status = status;
      this.name = 'ApiError';
    }
  },
}));

vi.mock('@/hooks/useRepoMcpConfig', () => ({
  repoMcpKeys: { detail: (id: string) => ['repo-mcp', 'detail', id] },
}));

vi.mock('@/hooks/useAgents', () => ({
  agentKeys: { list: (id: string) => ['agents', 'list', id] },
}));

vi.mock('@/utils/rateLimit', () => ({
  isRateLimitApiError: vi.fn(() => false),
}));

vi.mock('sonner', () => ({
  toast: sonnerMocks.toast,
}));

import * as api from '@/services/api';
import { toolKeys, useToolsList, useUndoableDeleteTool } from './useTools';

const mockToolsApi = api.toolsApi as unknown as {
  list: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  sync: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
  return { queryClient, wrapper };
}

const mockToolsResponse = {
  tools: [
    { id: 'tool-1', name: 'My Tool', server_url: 'https://mcp.example.com' },
  ],
};

describe('useToolsList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('returns tools list on success', async () => {
    mockToolsApi.list.mockResolvedValue(mockToolsResponse);

    const { result } = renderHook(() => useToolsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.tools).toEqual(mockToolsResponse.tools);
    expect(result.current.error).toBeNull();
  });

  it('does not fetch when projectId is null', () => {
    renderHook(() => useToolsList(null), { wrapper: createWrapper().wrapper });
    expect(mockToolsApi.list).not.toHaveBeenCalled();
  });

  it('returns empty tools when no data', async () => {
    mockToolsApi.list.mockResolvedValue({ tools: [] });

    const { result } = renderHook(() => useToolsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.tools).toEqual([]);
  });

  it('exposes error message on failure', async () => {
    mockToolsApi.list.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useToolsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.error).toBe('Network error'));
  });

  it('detects 401 auth error', async () => {
    const err = new api.ApiError(401, { error: 'Unauthorized' });
    mockToolsApi.list.mockRejectedValue(err);

    const { result } = renderHook(() => useToolsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.authError).toBe(true);
  });

  it('exposes mutation functions', async () => {
    mockToolsApi.list.mockResolvedValue(mockToolsResponse);

    const { result } = renderHook(() => useToolsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(typeof result.current.uploadTool).toBe('function');
    expect(typeof result.current.syncTool).toBe('function');
    expect(typeof result.current.updateTool).toBe('function');
    expect(typeof result.current.deleteTool).toBe('function');
  });

  it('restores cached tool lists when the confirmed delete result is unsuccessful', async () => {
    vi.useFakeTimers();
    mockToolsApi.delete.mockResolvedValue({
      success: false,
      deleted_id: null,
      affected_agents: [],
    });

    const { queryClient, wrapper } = createWrapper();
    const listKey = toolKeys.list('proj-1');
    const paginatedKey = [...listKey, 'paginated'];
    const listSnapshot = {
      tools: [
        { id: 'tool-1', name: 'My Tool', description: 'desc' },
        { id: 'tool-2', name: 'Other Tool', description: 'desc' },
      ],
    };
    const paginatedSnapshot = {
      pages: [
        {
          items: [
            { id: 'tool-1', name: 'My Tool', description: 'desc' },
            { id: 'tool-2', name: 'Other Tool', description: 'desc' },
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

    const { result } = renderHook(() => useUndoableDeleteTool('proj-1'), { wrapper });

    act(() => {
      result.current.deleteTool('tool-1', 'My Tool');
    });

    expect(queryClient.getQueryData(listKey)).toEqual({
      tools: [{ id: 'tool-2', name: 'Other Tool', description: 'desc' }],
    });
    expect(queryClient.getQueryData(paginatedKey)).toEqual({
      pages: [
        {
          items: [{ id: 'tool-2', name: 'Other Tool', description: 'desc' }],
          next_cursor: null,
          has_more: false,
          total_count: 2,
        },
      ],
      pageParams: [undefined],
    });

    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockToolsApi.delete).toHaveBeenCalledWith('proj-1', 'tool-1', true);
    expect(queryClient.getQueryData(listKey)).toEqual(listSnapshot);
    expect(queryClient.getQueryData(paginatedKey)).toEqual(paginatedSnapshot);
  });
});
