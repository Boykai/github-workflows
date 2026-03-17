import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePipelineModelOverride } from './usePipelineModelOverride';
import type { PipelineConfig } from '@/types';

function makePipeline(overrides: Partial<PipelineConfig> = {}): PipelineConfig {
  return {
    id: 'pipe-1',
    name: 'Test Pipeline',
    description: '',
    stages: [],
    created_at: '',
    updated_at: '',
    ...overrides,
  } as PipelineConfig;
}

function makeAgent(modelId: string, modelName: string) {
  return {
    id: `agent-${modelId}`,
    agent_slug: 'coder',
    agent_display_name: 'Coder',
    model_id: modelId,
    model_name: modelName,
    tool_ids: [],
    tool_count: 0,
    config: {},
  };
}

function makeStage(agents: ReturnType<typeof makeAgent>[], groups = true) {
  const base = {
    id: 'stage-1',
    name: 'Stage 1',
    order: 0,
    agents,
  };
  if (groups) {
    return { ...base, groups: [{ id: 'g1', order: 0, execution_mode: 'sequential' as const, agents }] };
  }
  return { ...base, groups: [] };
}

describe('usePipelineModelOverride', () => {
  it('returns auto mode when pipeline is null', () => {
    const setPipeline = vi.fn();
    const { result } = renderHook(() => usePipelineModelOverride(null, setPipeline));
    expect(result.current.modelOverride).toEqual({ mode: 'auto', modelId: '', modelName: '' });
  });

  it('returns auto mode when pipeline has no agents', () => {
    const setPipeline = vi.fn();
    const pipeline = makePipeline({ stages: [makeStage([])] });
    const { result } = renderHook(() => usePipelineModelOverride(pipeline, setPipeline));
    expect(result.current.modelOverride).toEqual({ mode: 'auto', modelId: '', modelName: '' });
  });

  it('returns specific mode when all agents use same model', () => {
    const setPipeline = vi.fn();
    const agents = [makeAgent('gpt-4', 'GPT-4'), makeAgent('gpt-4', 'GPT-4')];
    const pipeline = makePipeline({ stages: [makeStage(agents)] });
    const { result } = renderHook(() => usePipelineModelOverride(pipeline, setPipeline));
    expect(result.current.modelOverride.mode).toBe('specific');
    expect(result.current.modelOverride.modelId).toBe('gpt-4');
    expect(result.current.modelOverride.modelName).toBe('GPT-4');
  });

  it('returns mixed mode when agents use different models', () => {
    const setPipeline = vi.fn();
    const agents = [makeAgent('gpt-4', 'GPT-4'), makeAgent('claude-3', 'Claude 3')];
    const pipeline = makePipeline({ stages: [makeStage(agents)] });
    const { result } = renderHook(() => usePipelineModelOverride(pipeline, setPipeline));
    expect(result.current.modelOverride.mode).toBe('mixed');
  });

  it('setModelOverride updates all agents in pipeline', () => {
    let currentPipeline = makePipeline({
      stages: [makeStage([makeAgent('gpt-4', 'GPT-4')])],
    });
    const setPipeline = vi.fn((updater) => {
      if (typeof updater === 'function') {
        currentPipeline = updater(currentPipeline);
      }
    });

    const { result } = renderHook(() => usePipelineModelOverride(currentPipeline, setPipeline));

    act(() => {
      result.current.setModelOverride({
        mode: 'specific',
        modelId: 'claude-3',
        modelName: 'Claude 3',
      });
    });

    expect(setPipeline).toHaveBeenCalled();
    // Verify the updater modified agent models
    expect(currentPipeline.stages[0].agents[0].model_id).toBe('claude-3');
    expect(currentPipeline.stages[0].agents[0].model_name).toBe('Claude 3');
  });

  it('setModelOverride clears model when mode is auto', () => {
    let currentPipeline = makePipeline({
      stages: [makeStage([makeAgent('gpt-4', 'GPT-4')])],
    });
    const setPipeline = vi.fn((updater) => {
      if (typeof updater === 'function') {
        currentPipeline = updater(currentPipeline);
      }
    });

    const { result } = renderHook(() => usePipelineModelOverride(currentPipeline, setPipeline));

    act(() => {
      result.current.setModelOverride({ mode: 'auto', modelId: '', modelName: '' });
    });

    expect(currentPipeline.stages[0].agents[0].model_id).toBe('');
    expect(currentPipeline.stages[0].agents[0].model_name).toBe('');
  });

  it('resetPending clears the pending override', () => {
    const setPipeline = vi.fn();
    const pipeline = makePipeline({ stages: [] });
    const { result } = renderHook(() => usePipelineModelOverride(pipeline, setPipeline));

    // Set a pending override (no agents, so pending takes effect)
    act(() => {
      result.current.setModelOverride({ mode: 'specific', modelId: 'gpt-4', modelName: 'GPT-4' });
    });
    expect(result.current.modelOverride.mode).toBe('specific');

    act(() => {
      result.current.resetPending();
    });
    expect(result.current.modelOverride.mode).toBe('auto');
  });

  it('returns auto mode when all agents have empty model_id', () => {
    const setPipeline = vi.fn();
    const agents = [makeAgent('', ''), makeAgent('', '')];
    const pipeline = makePipeline({ stages: [makeStage(agents)] });
    const { result } = renderHook(() => usePipelineModelOverride(pipeline, setPipeline));
    expect(result.current.modelOverride.mode).toBe('auto');
  });
});
