import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  modelsApi: {
    list: vi.fn(),
  },
  settingsApi: {
    fetchModels: vi.fn(),
  },
}));

import * as api from '@/services/api';
import { useModels } from './useModels';

const mockModelsApi = api.modelsApi as unknown as {
  list: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockModels = [
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai' },
  { id: 'claude-3-5', name: 'Claude 3.5', provider: 'anthropic' },
];

describe('useModels', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns model list on success', async () => {
    mockModelsApi.list.mockResolvedValue(mockModels);

    const { result } = renderHook(() => useModels(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.models).toEqual(mockModels);
    expect(result.current.error).toBeNull();
  });

  it('groups models by provider', async () => {
    mockModelsApi.list.mockResolvedValue(mockModels);

    const { result } = renderHook(() => useModels(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.models.length).toBe(3));

    const groups = result.current.modelsByProvider;
    expect(groups).toHaveLength(2);

    const openaiGroup = groups.find((g) => g.provider === 'openai');
    expect(openaiGroup?.models).toHaveLength(2);

    const anthropicGroup = groups.find((g) => g.provider === 'anthropic');
    expect(anthropicGroup?.models).toHaveLength(1);
  });

  it('returns empty array when no data', async () => {
    mockModelsApi.list.mockResolvedValue([]);

    const { result } = renderHook(() => useModels(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.models).toEqual([]);
    expect(result.current.modelsByProvider).toEqual([]);
  });

  it('returns error message on failure', async () => {
    mockModelsApi.list.mockRejectedValue(new Error('Unable to load models'));

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    // Override retry at QueryClient level; the hook sets retry:2 but
    // we need immediate failure for testing
    function FailWrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    }

    const { result } = renderHook(() => useModels(), {
      wrapper: FailWrapper,
    });

    await waitFor(() => expect(result.current.error).toBe('Unable to load models'), {
      timeout: 5000,
    });
    expect(result.current.models).toEqual([]);
  });

  it('exposes refreshModels function', async () => {
    mockModelsApi.list.mockResolvedValue(mockModels);

    const { result } = renderHook(() => useModels(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(typeof result.current.refreshModels).toBe('function');
  });
});
