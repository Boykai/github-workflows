import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePipelineBoardMutations } from './usePipelineBoardMutations';
import type { PipelineConfig, PipelineStage, PipelineModelOverride, AvailableAgent } from '@/types';

vi.mock('@/utils/generateId', () => ({
  generateId: vi.fn(() => 'generated-id'),
}));

function makeAgent(id: string, slug = 'coder') {
  return {
    id,
    agent_slug: slug,
    agent_display_name: slug.charAt(0).toUpperCase() + slug.slice(1),
    model_id: 'gpt-4',
    model_name: 'GPT-4',
    tool_ids: [],
    tool_count: 0,
    config: {},
  };
}

function makeStage(id: string, agents = [makeAgent('a1')]): PipelineStage {
  return {
    id,
    name: `Stage ${id}`,
    order: 0,
    agents,
    groups: [{ id: 'g1', order: 0, execution_mode: 'sequential', agents }],
  } as PipelineStage;
}

function makePipeline(stages: PipelineStage[] = [makeStage('s1')]): PipelineConfig {
  return {
    id: 'pipe-1',
    name: 'Test Pipeline',
    description: '',
    stages,
    created_at: '',
    updated_at: '',
  } as PipelineConfig;
}

const autoOverride: PipelineModelOverride = { mode: 'auto', modelId: '', modelName: '' };
const specificOverride: PipelineModelOverride = { mode: 'specific', modelId: 'gpt-4', modelName: 'GPT-4' };

describe('usePipelineBoardMutations', () => {
  let pipeline: PipelineConfig | null;
  let setPipeline: ReturnType<typeof vi.fn>;
  let clearValidationError: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    pipeline = makePipeline();
    setPipeline = vi.fn((updater) => {
      if (typeof updater === 'function') {
        pipeline = updater(pipeline);
      } else {
        pipeline = updater;
      }
    });
    clearValidationError = vi.fn();
    vi.clearAllMocks();
  });

  it('setPipelineName updates name and clears validation error', () => {
    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.setPipelineName('New Name');
    });

    expect(pipeline?.name).toBe('New Name');
    expect(clearValidationError).toHaveBeenCalledWith('name');
  });

  it('setPipelineDescription updates description', () => {
    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.setPipelineDescription('New description');
    });

    expect(pipeline?.description).toBe('New description');
  });

  it('removeStage removes a stage and reorders', () => {
    pipeline = makePipeline([makeStage('s1'), makeStage('s2')]);

    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.removeStage('s1');
    });

    expect(pipeline?.stages).toHaveLength(1);
    expect(pipeline?.stages[0].id).toBe('s2');
    expect(pipeline?.stages[0].order).toBe(0);
  });

  it('updateStage updates stage properties', () => {
    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.updateStage('s1', { name: 'Updated Stage' });
    });

    expect(pipeline?.stages[0].name).toBe('Updated Stage');
  });

  it('addAgentToStage adds agent to existing group', () => {
    const mockAvailableAgent: AvailableAgent = {
      slug: 'reviewer',
      display_name: 'Reviewer',
      default_model_id: 'gpt-4',
      default_model_name: 'GPT-4',
    } as AvailableAgent;

    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.addAgentToStage('s1', mockAvailableAgent);
    });

    // Agent added to the first group
    const groups = pipeline?.stages[0].groups ?? [];
    expect(groups[0].agents).toHaveLength(2);
    expect(groups[0].agents[1].agent_slug).toBe('reviewer');
  });

  it('addAgentToStage uses specific model override', () => {
    pipeline = makePipeline([makeStage('s1', [])]);
    pipeline.stages[0].groups = [{ id: 'g1', order: 0, execution_mode: 'sequential' as const, agents: [] }];

    const mockAvailableAgent: AvailableAgent = {
      slug: 'coder',
      display_name: 'Coder',
      default_model_id: 'claude',
      default_model_name: 'Claude',
    } as AvailableAgent;

    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, specificOverride, clearValidationError),
    );

    act(() => {
      result.current.addAgentToStage('s1', mockAvailableAgent);
    });

    const agent = pipeline?.stages[0].groups?.[0].agents[0];
    expect(agent?.model_id).toBe('gpt-4');
    expect(agent?.model_name).toBe('GPT-4');
  });

  it('removeAgentFromStage removes agent from group', () => {
    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.removeAgentFromStage('s1', 'a1');
    });

    const groups = pipeline?.stages[0].groups ?? [];
    expect(groups[0].agents).toHaveLength(0);
    expect(pipeline?.stages[0].agents).toHaveLength(0);
  });

  it('cloneAgentInStage duplicates an agent', () => {
    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.cloneAgentInStage('s1', 'a1');
    });

    const groups = pipeline?.stages[0].groups ?? [];
    expect(groups[0].agents).toHaveLength(2);
    expect(groups[0].agents[1].id).toBe('generated-id');
    expect(groups[0].agents[1].agent_slug).toBe('coder');
  });

  it('addGroupToStage adds a new empty group', () => {
    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.addGroupToStage('s1');
    });

    const groups = pipeline?.stages[0].groups ?? [];
    expect(groups).toHaveLength(2);
    expect(groups[1].agents).toHaveLength(0);
  });

  it('removeGroupFromStage only removes empty groups', () => {
    // The first group has agents, so removal should be prevented
    pipeline = makePipeline([makeStage('s1')]);

    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.removeGroupFromStage('s1', 'g1');
    });

    // Group with agents should NOT be removed
    expect(pipeline?.stages[0].groups).toHaveLength(1);
  });

  it('updateGroupExecutionMode changes execution mode', () => {
    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.updateGroupExecutionMode('s1', 'g1', 'parallel');
    });

    expect(pipeline?.stages[0].groups?.[0].execution_mode).toBe('parallel');
  });

  it('returns null if pipeline is null for mutations', () => {
    pipeline = null;

    const { result } = renderHook(() =>
      usePipelineBoardMutations(setPipeline, autoOverride, clearValidationError),
    );

    act(() => {
      result.current.setPipelineName('Name');
    });

    expect(pipeline).toBeNull();
  });
});
