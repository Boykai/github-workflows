import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  workflowApi: {
    getConfig: vi.fn(),
    updateConfig: vi.fn(),
    listAgents: vi.fn(),
  },
}));

vi.mock('./useWorkflow', () => ({
  useWorkflow: () => ({
    updateConfig: mockUpdateConfig,
  }),
}));

vi.mock('@/utils/generateId', () => ({
  generateId: vi.fn(() => 'gen-id'),
}));

vi.mock('@/lib/case-utils', () => ({
  caseInsensitiveKey: (obj: Record<string, unknown>, key: string) => {
    const lower = key.toLowerCase();
    return Object.keys(obj).find((k) => k.toLowerCase() === lower) ?? key;
  },
}));

import * as api from '@/services/api';
import { useAgentConfig, useAvailableAgents } from './useAgentConfig';

const mockWorkflowApi = api.workflowApi as unknown as {
  getConfig: ReturnType<typeof vi.fn>;
  updateConfig: ReturnType<typeof vi.fn>;
  listAgents: ReturnType<typeof vi.fn>;
};

const mockUpdateConfig = vi.fn();

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockAgent = {
  slug: 'coder',
  display_name: 'Coder Agent',
  default_model_id: 'gpt-4',
  default_model_name: 'GPT-4',
};

const mockConfig = {
  agent_mappings: {
    'Todo': [{ id: 'a1', slug: 'coder', display_name: 'Coder', config: null }],
    'Done': [],
  },
};

describe('useAgentConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockWorkflowApi.getConfig.mockResolvedValue(mockConfig);
  });

  it('loads config when projectId is provided', async () => {
    const { result } = renderHook(() => useAgentConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoaded).toBe(true));
    expect(result.current.localMappings).toHaveProperty('Todo');
    expect(result.current.localMappings['Todo']).toHaveLength(1);
  });

  it('does not load config when projectId is null', () => {
    const { result } = renderHook(() => useAgentConfig(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoaded).toBe(false);
    expect(result.current.localMappings).toEqual({});
  });

  it('isDirty is false after initial load', async () => {
    const { result } = renderHook(() => useAgentConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoaded).toBe(true));
    expect(result.current.isDirty).toBe(false);
  });

  it('addAgent marks state as dirty', async () => {
    const { result } = renderHook(() => useAgentConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoaded).toBe(true));

    act(() => {
      result.current.addAgent('Todo', mockAgent as never);
    });

    expect(result.current.isDirty).toBe(true);
    expect(result.current.localMappings['Todo']).toHaveLength(2);
  });

  it('removeAgent removes by instance ID', async () => {
    const { result } = renderHook(() => useAgentConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoaded).toBe(true));

    act(() => {
      result.current.removeAgent('Todo', 'a1');
    });

    expect(result.current.localMappings['Todo']).toHaveLength(0);
  });

  it('discard resets local state to server state', async () => {
    const { result } = renderHook(() => useAgentConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoaded).toBe(true));

    act(() => {
      result.current.addAgent('Todo', mockAgent as never);
    });
    expect(result.current.isDirty).toBe(true);

    act(() => {
      result.current.discard();
    });

    expect(result.current.isDirty).toBe(false);
    expect(result.current.localMappings['Todo']).toHaveLength(1);
  });

  it('applyPreset updates local mappings', async () => {
    const { result } = renderHook(() => useAgentConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoaded).toBe(true));

    act(() => {
      result.current.applyPreset({
        'Todo': [{ id: 'p1', slug: 'reviewer', display_name: 'Reviewer', config: null }],
      } as never);
    });

    expect(result.current.localMappings['Todo']).toHaveLength(1);
    expect(result.current.localMappings['Todo'][0].slug).toBe('reviewer');
  });

  it('deduplicates case-variant status keys', async () => {
    mockWorkflowApi.getConfig.mockResolvedValue({
      agent_mappings: {
        'In Progress': [{ id: 'a1', slug: 'coder', display_name: 'Coder', config: null }],
        'in progress': [],
      },
    });

    const { result } = renderHook(() => useAgentConfig('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoaded).toBe(true));
    // Should keep the one with agents
    const keys = Object.keys(result.current.localMappings);
    const inProgressKeys = keys.filter((k) => k.toLowerCase() === 'in progress');
    expect(inProgressKeys).toHaveLength(1);
    expect(result.current.localMappings[inProgressKeys[0]]).toHaveLength(1);
  });
});

describe('useAvailableAgents', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns agents on success', async () => {
    mockWorkflowApi.listAgents.mockResolvedValue({ agents: [mockAgent] });

    const { result } = renderHook(() => useAvailableAgents('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.agents).toEqual([mockAgent]);
  });

  it('does not fetch when projectId is null', () => {
    const { result } = renderHook(() => useAvailableAgents(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.agents).toEqual([]);
    expect(mockWorkflowApi.listAgents).not.toHaveBeenCalled();
  });

  it('returns empty agents before data loads', () => {
    mockWorkflowApi.listAgents.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useAvailableAgents('proj-1'), {
      wrapper: createWrapper(),
    });

    expect(result.current.agents).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it('exposes error message on failure', async () => {
    mockWorkflowApi.listAgents.mockRejectedValue(new Error('API failed'));

    const { result } = renderHook(() => useAvailableAgents('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.error).toBe('API failed');
  });
});
