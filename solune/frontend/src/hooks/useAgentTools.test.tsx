import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  agentToolsApi: {
    getTools: vi.fn(),
    updateTools: vi.fn(),
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

import * as api from '@/services/api';
import { useAgentTools, agentToolKeys } from './useAgentTools';

const mockAgentToolsApi = api.agentToolsApi as unknown as {
  getTools: ReturnType<typeof vi.fn>;
  updateTools: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockTools = [
  { id: 'tool-1', name: 'GitHub Search' },
  { id: 'tool-2', name: 'File Reader' },
];

describe('useAgentTools', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns tools on success', async () => {
    mockAgentToolsApi.getTools.mockResolvedValue({ tools: mockTools });

    const { result } = renderHook(() => useAgentTools('proj-1', 'agent-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.tools).toEqual(mockTools);
  });

  it('does not fetch when projectId is null', () => {
    renderHook(() => useAgentTools(null, 'agent-1'), { wrapper: createWrapper() });
    expect(mockAgentToolsApi.getTools).not.toHaveBeenCalled();
  });

  it('does not fetch when agentId is null', () => {
    renderHook(() => useAgentTools('proj-1', null), { wrapper: createWrapper() });
    expect(mockAgentToolsApi.getTools).not.toHaveBeenCalled();
  });

  it('returns empty tools when no data', async () => {
    mockAgentToolsApi.getTools.mockResolvedValue({ tools: [] });

    const { result } = renderHook(() => useAgentTools('proj-1', 'agent-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.tools).toEqual([]);
  });

  it('calls updateTools mutation', async () => {
    mockAgentToolsApi.getTools.mockResolvedValue({ tools: mockTools });
    mockAgentToolsApi.updateTools.mockResolvedValue({ tools: mockTools });

    const { result } = renderHook(() => useAgentTools('proj-1', 'agent-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.updateTools(['tool-1', 'tool-3']);
    });

    expect(mockAgentToolsApi.updateTools).toHaveBeenCalledWith('proj-1', 'agent-1', [
      'tool-1',
      'tool-3',
    ]);
  });

  it('has correct query keys', () => {
    expect(agentToolKeys.tools('agent-1')).toEqual(['agents', 'agent-1', 'tools']);
  });

  it('exposes isUpdating state', async () => {
    mockAgentToolsApi.getTools.mockResolvedValue({ tools: mockTools });

    const { result } = renderHook(() => useAgentTools('proj-1', 'agent-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isUpdating).toBe(false);
  });

  it('returns empty tools array before data is available', () => {
    mockAgentToolsApi.getTools.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useAgentTools('proj-1', 'agent-1'), {
      wrapper: createWrapper(),
    });

    expect(result.current.tools).toEqual([]);
  });
});
