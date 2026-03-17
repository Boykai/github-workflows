import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePipelineValidation } from './usePipelineValidation';
import type { PipelineConfig } from '@/types';

function makePipeline(overrides: Partial<PipelineConfig> = {}): PipelineConfig {
  return {
    id: 'pipe-1',
    name: 'My Pipeline',
    description: '',
    stages: [],
    created_at: '',
    updated_at: '',
    ...overrides,
  } as PipelineConfig;
}

describe('usePipelineValidation', () => {
  it('returns no errors for a valid pipeline', () => {
    const { result } = renderHook(() => usePipelineValidation(makePipeline()));
    let isValid = false;
    act(() => {
      isValid = result.current.validatePipeline();
    });
    expect(isValid).toBe(true);
    expect(result.current.validationErrors).toEqual({});
  });

  it('returns name error when pipeline name is empty', () => {
    const { result } = renderHook(() => usePipelineValidation(makePipeline({ name: '' })));
    let isValid = true;
    act(() => {
      isValid = result.current.validatePipeline();
    });
    expect(isValid).toBe(false);
    expect(result.current.validationErrors.name).toBe('Pipeline name is required');
  });

  it('returns name error when pipeline name is whitespace', () => {
    const { result } = renderHook(() => usePipelineValidation(makePipeline({ name: '   ' })));
    let isValid = true;
    act(() => {
      isValid = result.current.validatePipeline();
    });
    expect(isValid).toBe(false);
    expect(result.current.validationErrors.name).toBe('Pipeline name is required');
  });

  it('returns name error when pipeline is null', () => {
    const { result } = renderHook(() => usePipelineValidation(null));
    let isValid = true;
    act(() => {
      isValid = result.current.validatePipeline();
    });
    expect(isValid).toBe(false);
    expect(result.current.validationErrors.name).toBe('Pipeline name is required');
  });

  it('clears a specific validation error', () => {
    const { result } = renderHook(() => usePipelineValidation(makePipeline({ name: '' })));
    act(() => {
      result.current.validatePipeline();
    });
    expect(result.current.validationErrors.name).toBeDefined();
    act(() => {
      result.current.clearValidationError('name');
    });
    expect(result.current.validationErrors.name).toBeUndefined();
  });

  it('clearValidationError is no-op for non-existent field', () => {
    const { result } = renderHook(() => usePipelineValidation(makePipeline({ name: '' })));
    act(() => {
      result.current.validatePipeline();
    });
    const errorsBefore = { ...result.current.validationErrors };
    act(() => {
      result.current.clearValidationError('nonexistent');
    });
    expect(result.current.validationErrors).toEqual(errorsBefore);
  });

  it('re-validates correctly after fixing the error', () => {
    const { result, rerender } = renderHook(
      ({ pipeline }) => usePipelineValidation(pipeline),
      { initialProps: { pipeline: makePipeline({ name: '' }) } },
    );
    act(() => {
      result.current.validatePipeline();
    });
    expect(result.current.validationErrors.name).toBeDefined();

    rerender({ pipeline: makePipeline({ name: 'Fixed Name' }) });
    let isValid = false;
    act(() => {
      isValid = result.current.validatePipeline();
    });
    expect(isValid).toBe(true);
    expect(result.current.validationErrors).toEqual({});
  });
});
