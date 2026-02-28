/**
 * Unit tests for useWorkflow hook.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWorkflow } from './useWorkflow';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  workflowApi: {
    confirmRecommendation: vi.fn(),
    rejectRecommendation: vi.fn(),
    getConfig: vi.fn(),
    updateConfig: vi.fn(),
  },
}));

const mockWorkflowApi = api.workflowApi as unknown as {
  confirmRecommendation: ReturnType<typeof vi.fn>;
  rejectRecommendation: ReturnType<typeof vi.fn>;
  getConfig: ReturnType<typeof vi.fn>;
  updateConfig: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useWorkflow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should not be loading initially', () => {
    const { result } = renderHook(() => useWorkflow(), {
      wrapper: createWrapper(),
    });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should confirm a recommendation', async () => {
    const mockResult = { status: 'confirmed', issue_number: 42 };
    mockWorkflowApi.confirmRecommendation.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useWorkflow(), {
      wrapper: createWrapper(),
    });

    let confirmResult: unknown;
    await act(async () => {
      confirmResult = await result.current.confirmRecommendation('rec-1');
    });

    expect(mockWorkflowApi.confirmRecommendation).toHaveBeenCalledWith('rec-1');
    expect(confirmResult).toEqual(mockResult);
  });

  it('should reject a recommendation', async () => {
    mockWorkflowApi.rejectRecommendation.mockResolvedValue(undefined);

    const { result } = renderHook(() => useWorkflow(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.rejectRecommendation('rec-2');
    });

    expect(mockWorkflowApi.rejectRecommendation).toHaveBeenCalledWith('rec-2');
  });

  it('should fetch config on demand via getConfig', async () => {
    // Use a type-accurate WorkflowConfiguration shape so the test reflects
    // real API contracts (project_id, copilot_assignee, etc. are required).
    const mockConfig = {
      project_id: 'PVT_1',
      repository_owner: 'owner',
      repository_name: 'repo',
      copilot_assignee: 'Copilot',
      agent_mappings: {},
      status_backlog: 'Backlog',
      status_ready: 'Ready',
      status_in_progress: 'In Progress',
      status_in_review: 'In Review',
      enabled: true,
    };
    mockWorkflowApi.getConfig.mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useWorkflow(), {
      wrapper: createWrapper(),
    });

    // Config should be undefined initially (enabled: false)
    expect(result.current.config).toBeUndefined();

    let configResult: unknown;
    await act(async () => {
      configResult = await result.current.getConfig();
    });

    expect(mockWorkflowApi.getConfig).toHaveBeenCalled();
    expect(configResult).toEqual(mockConfig);
  });

  it('should update config', async () => {
    // Partial update payload — uses real WorkflowConfiguration fields.
    const updatedConfig = { enabled: false };
    mockWorkflowApi.updateConfig.mockResolvedValue(updatedConfig);

    const { result } = renderHook(() => useWorkflow(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.updateConfig(updatedConfig);
    });

    expect(mockWorkflowApi.updateConfig).toHaveBeenCalledWith(updatedConfig);
  });

  it('should surface errors from mutations', async () => {
    mockWorkflowApi.confirmRecommendation.mockRejectedValue(
      new Error('API failure'),
    );

    const { result } = renderHook(() => useWorkflow(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.confirmRecommendation('rec-bad');
      } catch {
        // Expected
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe('API failure');
    });
  });
});
