/**
 * Unit tests for useAgentConfig and useAvailableAgents hooks
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAgentConfig, useAvailableAgents } from './useAgentConfig';

// Mock useWorkflow
const mockGetConfig = vi.fn();
const mockUpdateConfig = vi.fn();
vi.mock('./useWorkflow', () => ({
  useWorkflow: () => ({
    getConfig: mockGetConfig,
    updateConfig: mockUpdateConfig,
    isLoading: false,
    error: null,
  }),
}));

// Mock global fetch for useAvailableAgents
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

// Mock crypto.randomUUID
Object.defineProperty(globalThis, 'crypto', {
  value: {
    randomUUID: () => 'test-uuid-' + Math.random().toString(36).slice(2, 8),
  },
});

describe('useAgentConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should initialize with empty state when no projectId', () => {
    const { result } = renderHook(() => useAgentConfig(null));
    expect(result.current.localMappings).toEqual({});
    expect(result.current.isDirty).toBe(false);
    expect(result.current.isLoaded).toBe(false);
  });

  it('loadConfig fetches and sets mappings', async () => {
    const config = {
      project_id: 'PVT_1',
      enabled: true,
      agent_mappings: {
        Todo: [{ id: '1', slug: 'copilot', display_name: 'Copilot' }],
        Done: [],
      },
    };
    mockGetConfig.mockResolvedValue(config);

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    expect(result.current.localMappings).toEqual(config.agent_mappings);
    expect(result.current.isDirty).toBe(false);
  });

  it('addAgent adds an agent to a column', async () => {
    mockGetConfig.mockResolvedValue({
      project_id: 'PVT_1',
      agent_mappings: { Todo: [] },
    });

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    act(() => {
      result.current.addAgent('Todo', {
        slug: 'copilot',
        display_name: 'Copilot',
        source: 'repository' as const,
      });
    });

    expect(result.current.localMappings.Todo).toHaveLength(1);
    expect(result.current.localMappings.Todo[0].slug).toBe('copilot');
    expect(result.current.isDirty).toBe(true);
  });

  it('removeAgent removes an agent by instance ID', async () => {
    mockGetConfig.mockResolvedValue({
      project_id: 'PVT_1',
      agent_mappings: {
        Todo: [{ id: 'inst-1', slug: 'copilot', display_name: 'Copilot' }],
      },
    });

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    act(() => {
      result.current.removeAgent('Todo', 'inst-1');
    });

    expect(result.current.localMappings.Todo).toHaveLength(0);
    expect(result.current.isDirty).toBe(true);
  });

  it('reorderAgents replaces the agents in a column', async () => {
    const agents = [
      { id: '1', slug: 'a', display_name: 'A' },
      { id: '2', slug: 'b', display_name: 'B' },
    ];
    mockGetConfig.mockResolvedValue({
      project_id: 'PVT_1',
      agent_mappings: { Todo: agents },
    });

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    const reversed = [...agents].reverse();
    act(() => {
      result.current.reorderAgents('Todo', reversed);
    });

    expect(result.current.localMappings.Todo[0].slug).toBe('b');
    expect(result.current.localMappings.Todo[1].slug).toBe('a');
    expect(result.current.isDirty).toBe(true);
  });

  it('applyPreset replaces mappings', async () => {
    mockGetConfig.mockResolvedValue({
      project_id: 'PVT_1',
      agent_mappings: { Todo: [], InProgress: [] },
    });

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    act(() => {
      result.current.applyPreset({
        Todo: [{ id: 'p1', slug: 'copilot', display_name: 'Copilot' }],
      });
    });

    expect(result.current.localMappings.Todo).toHaveLength(1);
    expect(result.current.localMappings.InProgress).toEqual([]);
    expect(result.current.isDirty).toBe(true);
  });

  it('isDirty is false when mappings match server', async () => {
    const mappings = {
      Todo: [{ id: '1', slug: 'copilot', display_name: 'Copilot' }],
    };
    mockGetConfig.mockResolvedValue({
      project_id: 'PVT_1',
      agent_mappings: mappings,
    });

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    expect(result.current.isDirty).toBe(false);
  });

  it('save sends updated config to server', async () => {
    const config = {
      project_id: 'PVT_1',
      enabled: true,
      agent_mappings: { Todo: [] },
    };
    mockGetConfig.mockResolvedValue(config);

    const updatedConfig = {
      ...config,
      agent_mappings: {
        Todo: [{ id: 'new-1', slug: 'copilot', display_name: 'Copilot' }],
      },
    };
    mockUpdateConfig.mockResolvedValue(updatedConfig);

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    act(() => {
      result.current.addAgent('Todo', {
        slug: 'copilot',
        display_name: 'Copilot',
        source: 'repository' as const,
      });
    });

    await act(async () => {
      await result.current.save();
    });

    expect(mockUpdateConfig).toHaveBeenCalled();
    expect(result.current.isSaving).toBe(false);
  });

  it('save handles errors', async () => {
    const config = {
      project_id: 'PVT_1',
      enabled: true,
      agent_mappings: { Todo: [] },
    };
    mockGetConfig.mockResolvedValue(config);
    mockUpdateConfig.mockRejectedValue(new Error('Save failed'));

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    act(() => {
      result.current.addAgent('Todo', {
        slug: 'copilot',
        display_name: 'Copilot',
        source: 'repository' as const,
      });
    });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.saveError).toBe('Save failed');
    expect(result.current.isSaving).toBe(false);
  });

  it('discard resets to server mappings', async () => {
    const mappings = { Todo: [{ id: '1', slug: 'copilot', display_name: 'Copilot' }] };
    mockGetConfig.mockResolvedValue({
      project_id: 'PVT_1',
      agent_mappings: mappings,
    });

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    // Make a local change
    act(() => {
      result.current.removeAgent('Todo', '1');
    });

    expect(result.current.isDirty).toBe(true);

    // Discard
    act(() => {
      result.current.discard();
    });

    expect(result.current.localMappings.Todo).toHaveLength(1);
    expect(result.current.isDirty).toBe(false);
  });

  it('isColumnDirty detects per-column changes', async () => {
    mockGetConfig.mockResolvedValue({
      project_id: 'PVT_1',
      agent_mappings: {
        Todo: [{ id: '1', slug: 'copilot', display_name: 'Copilot' }],
        Done: [],
      },
    });

    const { result } = renderHook(() => useAgentConfig('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    expect(result.current.isColumnDirty('Todo')).toBe(false);
    expect(result.current.isColumnDirty('Done')).toBe(false);

    act(() => {
      result.current.removeAgent('Todo', '1');
    });

    expect(result.current.isColumnDirty('Todo')).toBe(true);
    expect(result.current.isColumnDirty('Done')).toBe(false);
  });
});

describe('useAvailableAgents', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should fetch agents when projectId is provided', async () => {
    const agents = [
      { slug: 'copilot', display_name: 'Copilot', source: 'repository' },
    ];
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ agents }),
    });

    const { result } = renderHook(() => useAvailableAgents('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.agents).toEqual(agents);
    expect(result.current.error).toBeNull();
  });

  it('should handle fetch error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
    });

    const { result } = renderHook(() => useAvailableAgents('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toContain('Failed to fetch agents');
  });

  it('should not fetch when projectId is null', () => {
    const { result } = renderHook(() => useAvailableAgents(null));

    expect(result.current.agents).toEqual([]);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('refetch triggers a new fetch', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ agents: [] }),
    });

    const { result } = renderHook(() => useAvailableAgents('PVT_1'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          agents: [{ slug: 'new-agent', display_name: 'New', source: 'repository' }],
        }),
    });

    await act(async () => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.agents).toHaveLength(1);
    });

    expect(result.current.agents[0].slug).toBe('new-agent');
  });
});
