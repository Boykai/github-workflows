/**
 * Regression tests for usePipelineReducer.
 *
 * Bug: DISCARD_EDITING action called JSON.parse without try-catch, crashing
 * the reducer when savedSnapshot contained invalid JSON.
 */

import { describe, expect, it } from 'vitest';
import { pipelineReducer, computeSnapshot, initialState } from './usePipelineReducer';
import type { PipelineState } from './usePipelineReducer';
import type { PipelineConfig } from '@/types';

function makePipeline(overrides: Partial<PipelineConfig> = {}): PipelineConfig {
  return {
    name: 'Test Pipeline',
    description: 'A test',
    stages: [{ name: 'Backlog', description: '' }],
    ...overrides,
  } as PipelineConfig;
}

describe('pipelineReducer — DISCARD_EDITING', () => {
  it('restores pipeline from a valid savedSnapshot', () => {
    const pipeline = makePipeline({ name: 'Original' });
    const snapshot = computeSnapshot(makePipeline({ name: 'Saved' }));
    const state: PipelineState = {
      ...initialState,
      pipeline,
      editingPipelineId: 'p1',
      savedSnapshot: snapshot,
    };

    const next = pipelineReducer(state, { type: 'DISCARD_EDITING' });
    expect(next.pipeline?.name).toBe('Saved');
    expect(next.saveError).toBeNull();
  });

  it('returns an error state when savedSnapshot is invalid JSON instead of crashing', () => {
    const state: PipelineState = {
      ...initialState,
      pipeline: makePipeline(),
      editingPipelineId: 'p1',
      savedSnapshot: '{invalid json!!!',
    };

    // Before fix this would throw — now it sets saveError
    const next = pipelineReducer(state, { type: 'DISCARD_EDITING' });
    expect(next.saveError).toBe('Failed to restore saved pipeline state');
    // Pipeline should be unchanged
    expect(next.pipeline?.name).toBe('Test Pipeline');
  });

  it('returns state unchanged when savedSnapshot is null', () => {
    const state: PipelineState = {
      ...initialState,
      pipeline: makePipeline(),
      savedSnapshot: null,
    };

    const next = pipelineReducer(state, { type: 'DISCARD_EDITING' });
    expect(next).toBe(state);
  });
});
