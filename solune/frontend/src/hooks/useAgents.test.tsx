import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  agentsApi: {
    list: vi.fn(),
    pending: vi.fn(),
    clearPending: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    chat: vi.fn(),
    bulkUpdateModels: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error: { error: string }
    ) {
      super(error.error);
      this.name = 'ApiError';
    }
  },
}));

vi.mock('@/constants', () => ({
  STALE_TIME_PROJECTS: 0,
}));

vi.mock('sonner', () => ({
  toast: Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  }),
}));

import * as api from '@/services/api';
import {
  useAgentsList,
  usePendingAgentsList,
  useCreateAgent,
  useUpdateAgent,
  useDeleteAgent,
  useClearPendingAgents,
  useAgentChat,
  useBulkUpdateModels,
  agentKeys,
} from './useAgents';

const mockAgentsApi = api.agentsApi as unknown as {
  list: ReturnType<typeof vi.fn>;
  pending: ReturnType<typeof vi.fn>;
  clearPending: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
  chat: ReturnType<typeof vi.fn>;
  bulkUpdateModels: ReturnType<typeof vi.fn>;
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

const mockAgent = {
  id: 'agent-1',
  name: 'Test Agent',
  slug: 'test-agent',
  description: 'A test agent',
};

describe('useAgentsList', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns agent list on success', async () => {
    mockAgentsApi.list.mockResolvedValue([mockAgent]);

     const { result } = renderHook(() => useAgentsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockAgent]);
    expect(mockAgentsApi.list).toHaveBeenCalledWith('proj-1');
  });

  it('does not fetch when projectId is null', () => {
    renderHook(() => useAgentsList(null), { wrapper: createWrapper().wrapper });
    expect(mockAgentsApi.list).not.toHaveBeenCalled();
  });

  it('handles API error', async () => {
    mockAgentsApi.list.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAgentsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe('Network error');
  });
});

describe('usePendingAgentsList', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns pending agents list', async () => {
    mockAgentsApi.pending.mockResolvedValue([mockAgent]);

    const { result } = renderHook(() => usePendingAgentsList('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockAgent]);
  });
});

describe('useCreateAgent', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls create API and returns result', async () => {
    const createResult = { agent: mockAgent, message: 'Created' };
    mockAgentsApi.create.mockResolvedValue(createResult);

    const { result } = renderHook(() => useCreateAgent('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await act(async () => {
      await result.current.mutateAsync({ name: 'New Agent', description: 'Desc' } as never);
    });

    expect(mockAgentsApi.create).toHaveBeenCalledWith('proj-1', {
      name: 'New Agent',
      description: 'Desc',
    });
  });

  it('optimistically prepends to the pending cache on mutate', async () => {
    mockAgentsApi.create.mockImplementation(() => new Promise(() => {}));
    const { queryClient, wrapper } = createWrapper();
    const pendingKey = agentKeys.pending('proj-1');
    const existingPending = [{ id: 'agent-existing', name: 'Existing' }];
    queryClient.setQueryData(pendingKey, existingPending);

    const { result } = renderHook(() => useCreateAgent('proj-1'), { wrapper });

    act(() => {
      result.current.mutate({
        name: 'New Agent',
        system_prompt: 'prompt',
      } as never);
    });

    await waitFor(() => {
      const cache = queryClient.getQueryData<unknown[]>(pendingKey);
      expect(cache).toHaveLength(2);
      expect((cache![0] as Record<string, unknown>).name).toBe('New Agent');
      expect((cache![0] as Record<string, unknown>)._optimistic).toBe(true);
    });
  });

  it('restores pending cache on error', async () => {
    mockAgentsApi.create.mockRejectedValue(new Error('Boom'));
    const { queryClient, wrapper } = createWrapper();
    const pendingKey = agentKeys.pending('proj-1');
    const existingPending = [{ id: 'agent-existing', name: 'Existing' }];
    queryClient.setQueryData(pendingKey, existingPending);

    const { result } = renderHook(() => useCreateAgent('proj-1'), { wrapper });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          name: 'New Agent',
          system_prompt: 'prompt',
        } as never);
      } catch {
        // expected
      }
    });

    const cache = queryClient.getQueryData<unknown[]>(pendingKey);
    expect(cache).toEqual(existingPending);
  });

  it('clears optimistic placeholder on error when pending cache was empty', async () => {
    mockAgentsApi.create.mockRejectedValue(new Error('Boom'));
    const { queryClient, wrapper } = createWrapper();
    const pendingKey = agentKeys.pending('proj-1');
    // Do NOT seed the pending cache — it starts as undefined

    const { result } = renderHook(() => useCreateAgent('proj-1'), { wrapper });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          name: 'Ghost Agent',
          system_prompt: 'prompt',
        } as never);
      } catch {
        // expected
      }
    });

    // Cache should be restored to undefined (no data), not left with the optimistic placeholder
    const cache = queryClient.getQueryData<unknown[]>(pendingKey);
    expect(cache).toBeUndefined();
  });
});

describe('useUpdateAgent', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls update API', async () => {
    mockAgentsApi.update.mockResolvedValue({ agent: mockAgent, message: 'Updated' });

    const { result } = renderHook(() => useUpdateAgent('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await act(async () => {
      await result.current.mutateAsync({
        agentId: 'agent-1',
        data: { description: 'Updated' },
      } as never);
    });

    expect(mockAgentsApi.update).toHaveBeenCalledWith('proj-1', 'agent-1', {
      description: 'Updated',
    });
  });
});

describe('useDeleteAgent', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls delete API', async () => {
    mockAgentsApi.delete.mockResolvedValue({
      success: true,
      pr_url: 'https://example.test/pr/1',
      pr_number: 1,
      issue_number: null,
    });

    const { result } = renderHook(() => useDeleteAgent('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await act(async () => {
      await result.current.mutateAsync('agent-1');
    });

    expect(mockAgentsApi.delete).toHaveBeenCalledWith('proj-1', 'agent-1');
  });

  it('rejects when the delete API reports success false', async () => {
    mockAgentsApi.delete.mockResolvedValue({
      success: false,
      pr_url: 'https://example.test/pr/1',
      pr_number: 1,
      issue_number: null,
    });

    const { result } = renderHook(() => useDeleteAgent('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await expect(result.current.mutateAsync('agent-1')).rejects.toThrow(
      'Failed to delete agent "agent-1"',
    );
  });
});

describe('useClearPendingAgents', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls clearPending API', async () => {
    mockAgentsApi.clearPending.mockResolvedValue({ deleted: 2, message: 'Cleared' });

    const { result } = renderHook(() => useClearPendingAgents('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(mockAgentsApi.clearPending).toHaveBeenCalledWith('proj-1');
  });
});

describe('useAgentChat', () => {
  beforeEach(() => vi.clearAllMocks());

  it('sends chat message', async () => {
    const response = { message: 'Hello back', actions: [] };
    mockAgentsApi.chat.mockResolvedValue(response);

    const { result } = renderHook(() => useAgentChat('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await act(async () => {
      const res = await result.current.mutateAsync({ content: 'Hello' } as never);
      expect(res).toEqual(response);
    });
  });
});

describe('useBulkUpdateModels', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls bulkUpdateModels API', async () => {
    mockAgentsApi.bulkUpdateModels.mockResolvedValue({ updated: 3, message: 'Done' });

    const { result } = renderHook(() => useBulkUpdateModels('proj-1'), {
      wrapper: createWrapper().wrapper,
    });

    await act(async () => {
      await result.current.mutateAsync({
        targetModelId: 'model-1',
        targetModelName: 'GPT-4o',
      });
    });

    expect(mockAgentsApi.bulkUpdateModels).toHaveBeenCalledWith('proj-1', 'model-1', 'GPT-4o');
  });
});
