import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  mcpApi: {
    listMcps: vi.fn(),
    createMcp: vi.fn(),
    deleteMcp: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    error: { error: string };
    constructor(status: number, error: { error: string }) {
      super(error.error);
      this.status = status;
      this.error = error;
      this.name = 'ApiError';
    }
  },
}));

vi.mock('@/constants', () => ({
  STALE_TIME_LONG: 300_000,
}));

import * as api from '@/services/api';
import { useMcpSettings, mcpKeys } from './useMcpSettings';

const mockMcpApi = api.mcpApi as unknown as {
  listMcps: ReturnType<typeof vi.fn>;
  createMcp: ReturnType<typeof vi.fn>;
  deleteMcp: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockMcps = [
  { id: 'mcp-1', name: 'GitHub MCP', url: 'https://mcp1.example.com' },
  { id: 'mcp-2', name: 'Slack MCP', url: 'https://mcp2.example.com' },
];

describe('useMcpSettings', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns mcps on success', async () => {
    mockMcpApi.listMcps.mockResolvedValue({ mcps: mockMcps, count: 2 });

    const { result } = renderHook(() => useMcpSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.mcps).toEqual(mockMcps);
    expect(result.current.count).toBe(2);
  });

  it('returns empty mcps when no data', async () => {
    mockMcpApi.listMcps.mockResolvedValue({ mcps: [], count: 0 });

    const { result } = renderHook(() => useMcpSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.mcps).toEqual([]);
    expect(result.current.count).toBe(0);
  });

  it('creates an MCP', async () => {
    mockMcpApi.listMcps.mockResolvedValue({ mcps: [], count: 0 });
    mockMcpApi.createMcp.mockResolvedValue({ id: 'mcp-new', name: 'New MCP' });

    const { result } = renderHook(() => useMcpSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.createMcp({ name: 'New MCP', url: 'https://new.example.com' } as never);
    });

    expect(mockMcpApi.createMcp).toHaveBeenCalled();
  });

  it('deletes an MCP and tracks deletingId', async () => {
    mockMcpApi.listMcps.mockResolvedValue({ mcps: mockMcps, count: 2 });
    mockMcpApi.deleteMcp.mockResolvedValue({ message: 'deleted' });

    const { result } = renderHook(() => useMcpSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.deleteMcp('mcp-1');
    });

    expect(mockMcpApi.deleteMcp).toHaveBeenCalledWith('mcp-1');
    // deletingId is cleared after settle
    expect(result.current.deletingId).toBeNull();
  });

  it('detects 401 auth error from query', async () => {
    const err = new api.ApiError(401, { error: 'Unauthorized' });
    mockMcpApi.listMcps.mockRejectedValue(err);

    const { result } = renderHook(() => useMcpSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.authError).toBe(true);
  });

  it('authError is false for non-401 errors', async () => {
    mockMcpApi.listMcps.mockRejectedValue(new api.ApiError(500, { error: 'Server error' }));

    const { result } = renderHook(() => useMcpSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.authError).toBe(false);
  });

  it('has correct query keys', () => {
    expect(mcpKeys.all).toEqual(['mcp']);
    expect(mcpKeys.list()).toEqual(['mcp', 'list']);
  });

  it('exposes reset error functions', async () => {
    mockMcpApi.listMcps.mockResolvedValue({ mcps: [], count: 0 });

    const { result } = renderHook(() => useMcpSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(typeof result.current.resetCreateError).toBe('function');
    expect(typeof result.current.resetDeleteError).toBe('function');
  });
});
