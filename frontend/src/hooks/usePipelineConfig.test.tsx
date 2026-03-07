/**
 * Unit tests for usePipelineConfig hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { usePipelineConfig } from './usePipelineConfig';
import * as api from '../services/api';
import type { AvailableAgent, PipelineStage } from '../types';

vi.mock('@/services/api', () => ({
  pipelinesApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockPipelinesApi = api.pipelinesApi as unknown as {
  list: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('usePipelineConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPipelinesApi.list.mockResolvedValue({ pipelines: [], total: 0 });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('seeds a new pipeline from provided stage names', async () => {
    const { result } = renderHook(() => usePipelineConfig('PVT_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.pipelinesLoading).toBe(false);
    });

    act(() => {
      result.current.newPipeline(['Todo', 'In Progress', 'Done']);
    });

    expect(result.current.boardState).toBe('creating');
    expect(result.current.pipeline?.stages).toHaveLength(3);
    expect(result.current.pipeline?.stages.map((stage: PipelineStage) => stage.name)).toEqual([
      'Todo',
      'In Progress',
      'Done',
    ]);
    expect(result.current.pipeline?.stages.map((stage: PipelineStage) => stage.order)).toEqual([0, 1, 2]);
    expect(result.current.pipeline?.stages.every((stage: PipelineStage) => stage.agents.length === 0)).toBe(true);
  });

  it('creates an empty new pipeline when no stage names are provided', async () => {
    const { result } = renderHook(() => usePipelineConfig('PVT_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.pipelinesLoading).toBe(false);
    });

    act(() => {
      result.current.newPipeline();
    });

    expect(result.current.boardState).toBe('creating');
    expect(result.current.pipeline?.stages).toEqual([]);
  });

  it('uses an agent default model when adding the agent to a stage', async () => {
    const { result } = renderHook(() => usePipelineConfig('PVT_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.pipelinesLoading).toBe(false);
    });

    act(() => {
      result.current.newPipeline(['Inbox']);
    });

    const stageId = result.current.pipeline?.stages[0]?.id;
    expect(stageId).toBeTruthy();

    const agent: AvailableAgent = {
      slug: 'security-reviewer',
      display_name: 'Security Reviewer',
      source: 'repository',
      default_model_id: 'gpt-5.4-mini',
      default_model_name: 'GPT-5.4 Mini',
    };

    act(() => {
      result.current.addAgentToStage(stageId!, agent);
    });

    const stage = result.current.pipeline?.stages[0];
    expect(stage?.agents).toHaveLength(1);
    expect(stage?.agents[0]?.model_id).toBe('gpt-5.4-mini');
    expect(stage?.agents[0]?.model_name).toBe('GPT-5.4 Mini');
  });
});
