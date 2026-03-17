import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  toolsApi: {
    getRepoConfig: vi.fn(),
    updateRepoServer: vi.fn(),
    deleteRepoServer: vi.fn(),
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

import * as api from '@/services/api';
import { useRepoMcpConfig, repoMcpKeys } from './useRepoMcpConfig';

const mockToolsApi = api.toolsApi as unknown as {
  getRepoConfig: ReturnType<typeof vi.fn>;
  updateRepoServer: ReturnType<typeof vi.fn>;
  deleteRepoServer: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockRepoConfig = {
  servers: [
    { name: 'github-mcp', url: 'https://mcp.github.com', enabled: true },
  ],
};

describe('useRepoMcpConfig', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns repo config on success', async () => {
    mockToolsApi.getRepoConfig.mockResolvedValue(mockRepoConfig);

    const { result } = renderHook(() => useRepoMcpConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.repoConfig).toEqual(mockRepoConfig);
    expect(result.current.error).toBeNull();
  });

  it('does not fetch when projectId is null', () => {
    renderHook(() => useRepoMcpConfig(null), { wrapper: createWrapper() });
    expect(mockToolsApi.getRepoConfig).not.toHaveBeenCalled();
  });

  it('returns null repoConfig before data loads', () => {
    mockToolsApi.getRepoConfig.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useRepoMcpConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    expect(result.current.repoConfig).toBeNull();
  });

  it('updates a repo server', async () => {
    mockToolsApi.getRepoConfig.mockResolvedValue(mockRepoConfig);
    mockToolsApi.updateRepoServer.mockResolvedValue({ name: 'github-mcp', enabled: false });

    const { result } = renderHook(() => useRepoMcpConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.updateRepoServer({
        serverName: 'github-mcp',
        data: { enabled: false },
      });
    });

    expect(mockToolsApi.updateRepoServer).toHaveBeenCalledWith('proj-1', 'github-mcp', {
      enabled: false,
    });
    // updatingServerName should be cleared after settle
    expect(result.current.updatingServerName).toBeNull();
  });

  it('deletes a repo server', async () => {
    mockToolsApi.getRepoConfig.mockResolvedValue(mockRepoConfig);
    mockToolsApi.deleteRepoServer.mockResolvedValue({ name: 'github-mcp' });

    const { result } = renderHook(() => useRepoMcpConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.deleteRepoServer('github-mcp');
    });

    expect(mockToolsApi.deleteRepoServer).toHaveBeenCalledWith('proj-1', 'github-mcp');
    expect(result.current.deletingServerName).toBeNull();
  });

  it('exposes error message on failure', async () => {
    mockToolsApi.getRepoConfig.mockRejectedValue(
      new api.ApiError(500, { error: 'Server error' }),
    );

    const { result } = renderHook(() => useRepoMcpConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.error).toBe('Server error');
  });

  it('has correct query keys', () => {
    expect(repoMcpKeys.all).toEqual(['repo-mcp']);
    expect(repoMcpKeys.detail('proj-1')).toEqual(['repo-mcp', 'proj-1']);
  });

  it('exposes reset error functions', async () => {
    mockToolsApi.getRepoConfig.mockResolvedValue(mockRepoConfig);

    const { result } = renderHook(() => useRepoMcpConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(typeof result.current.resetUpdateError).toBe('function');
    expect(typeof result.current.resetDeleteError).toBe('function');
  });
});
