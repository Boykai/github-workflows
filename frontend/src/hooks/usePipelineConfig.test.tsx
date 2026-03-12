/**
 * Unit tests for usePipelineConfig hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { usePipelineConfig } from './usePipelineConfig';
import * as api from '@/services/api';
import type { AvailableAgent, PipelineStage } from '@/types';

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
    expect(result.current.pipeline?.stages.map((stage: PipelineStage) => stage.order)).toEqual([
      0, 1, 2,
    ]);
    expect(
      result.current.pipeline?.stages.every((stage: PipelineStage) => stage.agents.length === 0)
    ).toBe(true);
    expect(
      result.current.pipeline?.stages.every(
        (stage: PipelineStage) =>
          stage.groups?.length === 1 &&
          stage.groups[0]?.execution_mode === 'sequential' &&
          stage.groups[0]?.agents.length === 0
      )
    ).toBe(true);
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

  it('retains a selected pipeline model before any agents exist and applies it to future agents', async () => {
    const { result } = renderHook(() => usePipelineConfig('PVT_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.pipelinesLoading).toBe(false);
    });

    act(() => {
      result.current.newPipeline(['Inbox']);
    });

    act(() => {
      result.current.setModelOverride({
        mode: 'specific',
        modelId: 'gpt-5.4',
        modelName: 'GPT-5.4',
      });
    });

    expect(result.current.modelOverride).toEqual({
      mode: 'specific',
      modelId: 'gpt-5.4',
      modelName: 'GPT-5.4',
    });

    const stageId = result.current.pipeline?.stages[0]?.id;
    expect(stageId).toBeTruthy();

    const agent: AvailableAgent = {
      slug: 'writer',
      display_name: 'Writer',
      source: 'repository',
      default_model_id: 'gpt-5.4-mini',
      default_model_name: 'GPT-5.4 Mini',
    };

    act(() => {
      result.current.addAgentToStage(stageId!, agent);
    });

    const stage = result.current.pipeline?.stages[0];
    expect(stage?.agents).toHaveLength(1);
    expect(stage?.agents[0]?.model_id).toBe('gpt-5.4');
    expect(stage?.agents[0]?.model_name).toBe('GPT-5.4');
    expect(result.current.modelOverride).toEqual({
      mode: 'specific',
      modelId: 'gpt-5.4',
      modelName: 'GPT-5.4',
    });
  });

  it('moves an agent into another group without losing its configuration', async () => {
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
    const sourceGroupId = result.current.pipeline?.stages[0]?.groups?.[0]?.id;

    expect(stageId).toBeTruthy();
    expect(sourceGroupId).toBeTruthy();

    const agent: AvailableAgent = {
      slug: 'security-reviewer',
      display_name: 'Security Reviewer',
      source: 'repository',
      default_model_id: 'gpt-5.4-mini',
      default_model_name: 'GPT-5.4 Mini',
    };

    act(() => {
      result.current.addAgentToStage(stageId!, agent, sourceGroupId);
      result.current.addGroupToStage(stageId!);
    });

    const targetGroupId = result.current.pipeline?.stages[0]?.groups?.[1]?.id;
    const agentId = result.current.pipeline?.stages[0]?.groups?.[0]?.agents[0]?.id;

    expect(targetGroupId).toBeTruthy();
    expect(agentId).toBeTruthy();

    act(() => {
      result.current.updateAgentTools(stageId!, agentId!, ['tool-a', 'tool-b']);
      result.current.moveAgentToGroup(stageId!, stageId!, agentId!, targetGroupId!);
    });

    const stage = result.current.pipeline?.stages[0];
    expect(stage?.groups?.[0]?.agents).toEqual([]);
    expect(stage?.groups?.[1]?.agents).toHaveLength(1);
    expect(stage?.groups?.[1]?.agents[0]).toMatchObject({
      id: agentId,
      model_id: 'gpt-5.4-mini',
      model_name: 'GPT-5.4 Mini',
      tool_ids: ['tool-a', 'tool-b'],
      tool_count: 2,
    });
    expect(stage?.agents).toHaveLength(1);
    expect(stage?.agents[0]?.id).toBe(agentId);
  });

  it('adds an agent to the requested execution group instead of the first group', async () => {
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
    const firstGroupId = result.current.pipeline?.stages[0]?.groups?.[0]?.id;

    expect(stageId).toBeTruthy();
    expect(firstGroupId).toBeTruthy();

    act(() => {
      result.current.addGroupToStage(stageId!);
    });

    const secondGroupId = result.current.pipeline?.stages[0]?.groups?.[1]?.id;
    expect(secondGroupId).toBeTruthy();

    act(() => {
      result.current.addAgentToStage(
        stageId!,
        {
          slug: 'reviewer',
          display_name: 'Reviewer',
          source: 'repository',
          default_model_id: 'gpt-5.4-mini',
          default_model_name: 'GPT-5.4 Mini',
        },
        secondGroupId,
      );
    });

    const stage = result.current.pipeline?.stages[0];
    expect(stage?.groups?.[0]?.agents).toEqual([]);
    expect(stage?.groups?.[1]?.agents).toHaveLength(1);
    expect(stage?.groups?.[1]?.agents[0]).toMatchObject({
      agent_slug: 'reviewer',
      model_id: 'gpt-5.4-mini',
      model_name: 'GPT-5.4 Mini',
    });
    expect(stage?.agents).toEqual(stage?.groups?.[1]?.agents);
  });

  it('does not remove an agent when the target group does not exist', async () => {
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
    const sourceGroupId = result.current.pipeline?.stages[0]?.groups?.[0]?.id;

    expect(stageId).toBeTruthy();
    expect(sourceGroupId).toBeTruthy();

    act(() => {
      result.current.addAgentToStage(stageId!, {
        slug: 'copilot',
        display_name: 'GitHub Copilot',
        source: 'builtin',
      }, sourceGroupId);
    });

    const beforeMove = result.current.pipeline?.stages[0]?.groups?.[0]?.agents[0];
    expect(beforeMove).toBeTruthy();

    act(() => {
      result.current.moveAgentToGroup(stageId!, stageId!, beforeMove!.id, 'missing-group');
    });

    const stage = result.current.pipeline?.stages[0];
    expect(stage?.groups?.[0]?.agents).toHaveLength(1);
    expect(stage?.groups?.[0]?.agents[0]).toEqual(beforeMove);
    expect(stage?.agents).toHaveLength(1);
  });

  it('moves an agent across stages into the requested position and keeps flattened stage agents in sync', async () => {
    const { result } = renderHook(() => usePipelineConfig('PVT_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.pipelinesLoading).toBe(false);
    });

    act(() => {
      result.current.newPipeline(['Inbox', 'Review']);
    });

    const sourceStageId = result.current.pipeline?.stages[0]?.id;
    const targetStageId = result.current.pipeline?.stages[1]?.id;
    const sourceGroupId = result.current.pipeline?.stages[0]?.groups?.[0]?.id;
    const targetGroupId = result.current.pipeline?.stages[1]?.groups?.[0]?.id;

    expect(sourceStageId).toBeTruthy();
    expect(targetStageId).toBeTruthy();
    expect(sourceGroupId).toBeTruthy();
    expect(targetGroupId).toBeTruthy();

    act(() => {
      result.current.addAgentToStage(sourceStageId!, {
        slug: 'security-reviewer',
        display_name: 'Security Reviewer',
        source: 'repository',
        default_model_id: 'gpt-5.4-mini',
        default_model_name: 'GPT-5.4 Mini',
      }, sourceGroupId);
      result.current.addAgentToStage(targetStageId!, {
        slug: 'writer',
        display_name: 'Writer',
        source: 'repository',
        default_model_id: 'gpt-5.4',
        default_model_name: 'GPT-5.4',
      }, targetGroupId);
    });

    const sourceAgentId = result.current.pipeline?.stages[0]?.groups?.[0]?.agents[0]?.id;
    const existingTargetAgentId = result.current.pipeline?.stages[1]?.groups?.[0]?.agents[0]?.id;

    expect(sourceAgentId).toBeTruthy();
    expect(existingTargetAgentId).toBeTruthy();

    act(() => {
      result.current.updateAgentTools(sourceStageId!, sourceAgentId!, ['tool-a', 'tool-b']);
      result.current.moveAgentToGroup(sourceStageId!, targetStageId!, sourceAgentId!, targetGroupId!, 0);
    });

    const sourceStage = result.current.pipeline?.stages[0];
    const targetStage = result.current.pipeline?.stages[1];

    expect(sourceStage?.groups?.[0]?.agents).toEqual([]);
    expect(sourceStage?.agents).toEqual([]);
    expect(targetStage?.groups?.[0]?.agents.map((agent) => agent.id)).toEqual([
      sourceAgentId,
      existingTargetAgentId,
    ]);
    expect(targetStage?.groups?.[0]?.agents[0]).toMatchObject({
      id: sourceAgentId,
      model_id: 'gpt-5.4-mini',
      model_name: 'GPT-5.4 Mini',
      tool_ids: ['tool-a', 'tool-b'],
      tool_count: 2,
    });
    expect(targetStage?.agents.map((agent) => agent.id)).toEqual([
      sourceAgentId,
      existingTargetAgentId,
    ]);
  });
});
