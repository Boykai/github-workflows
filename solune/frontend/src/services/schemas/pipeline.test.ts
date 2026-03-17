import { describe, it, expect } from 'vitest';
import { PipelineStateInfoSchema } from './pipeline';

const validPipelineState = {
  issue_number: 42,
  project_id: 'PVT_abc',
  status: 'running',
  agents: ['agent-1', 'agent-2'],
  current_agent_index: 0,
  current_agent: 'agent-1',
  completed_agents: [],
  is_complete: false,
  started_at: '2024-01-01T00:00:00Z',
  error: null,
};

describe('PipelineStateInfoSchema', () => {
  it('parses valid pipeline state', () => {
    const result = PipelineStateInfoSchema.parse(validPipelineState);
    expect(result.issue_number).toBe(42);
    expect(result.agents).toEqual(['agent-1', 'agent-2']);
  });

  it('parses completed pipeline', () => {
    const data = {
      ...validPipelineState,
      is_complete: true,
      current_agent: null,
      completed_agents: ['agent-1', 'agent-2'],
      current_agent_index: 2,
    };
    const result = PipelineStateInfoSchema.parse(data);
    expect(result.is_complete).toBe(true);
    expect(result.current_agent).toBeNull();
  });

  it('accepts nullable current_agent', () => {
    const data = { ...validPipelineState, current_agent: null };
    expect(PipelineStateInfoSchema.parse(data).current_agent).toBeNull();
  });

  it('accepts nullable started_at', () => {
    const data = { ...validPipelineState, started_at: null };
    expect(PipelineStateInfoSchema.parse(data).started_at).toBeNull();
  });

  it('accepts nullable error', () => {
    const data = { ...validPipelineState, error: 'Agent failed' };
    expect(PipelineStateInfoSchema.parse(data).error).toBe('Agent failed');
  });

  it('parses empty agents array', () => {
    const data = { ...validPipelineState, agents: [], completed_agents: [] };
    expect(PipelineStateInfoSchema.parse(data).agents).toEqual([]);
  });

  it('rejects missing issue_number', () => {
    const { issue_number: _, ...rest } = validPipelineState;
    expect(() => PipelineStateInfoSchema.parse(rest)).toThrow();
  });

  it('rejects non-boolean is_complete', () => {
    const data = { ...validPipelineState, is_complete: 'yes' };
    expect(() => PipelineStateInfoSchema.parse(data)).toThrow();
  });

  it('rejects non-number current_agent_index', () => {
    const data = { ...validPipelineState, current_agent_index: 'zero' };
    expect(() => PipelineStateInfoSchema.parse(data)).toThrow();
  });
});
