import { QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createTestQueryClient } from '@/test/test-utils';
import { useSelectedPipeline } from './useSelectedPipeline';

const mockGetAssignment = vi.fn();
const mockList = vi.fn();

vi.mock('@/services/api', () => ({
  pipelinesApi: {
    getAssignment: (...args: unknown[]) => mockGetAssignment(...args),
    list: (...args: unknown[]) => mockList(...args),
  },
}));

function createWrapper() {
  const queryClient = createTestQueryClient();

  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

afterEach(() => {
  mockGetAssignment.mockReset();
  mockList.mockReset();
});

describe('useSelectedPipeline', () => {
  it('returns loading state while the queries are in flight', () => {
    const assignment = createDeferred<{ project_id: string; pipeline_id: string }>();
    const pipelines = createDeferred<{ pipelines: Array<{ id: string; name: string }> }>();
    mockGetAssignment.mockReturnValue(assignment.promise);
    mockList.mockReturnValue(pipelines.promise);

    const { result } = renderHook(() => useSelectedPipeline('project-1'), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.pipelineId).toBe('');
    expect(result.current.pipelineName).toBe('');
  });

  it('returns hasAssignment false when no pipeline is assigned', async () => {
    mockGetAssignment.mockResolvedValue({ project_id: 'project-1', pipeline_id: '' });
    mockList.mockResolvedValue({ pipelines: [] });

    const { result } = renderHook(() => useSelectedPipeline('project-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasAssignment).toBe(false);
    expect(result.current.pipelineId).toBe('');
    expect(result.current.pipelineName).toBe('');
  });

  it('resolves the pipeline name from the pipeline list', async () => {
    mockGetAssignment.mockResolvedValue({ project_id: 'project-1', pipeline_id: 'pipeline-1' });
    mockList.mockResolvedValue({
      pipelines: [
        { id: 'pipeline-1', name: 'Full Review Pipeline' },
        { id: 'pipeline-2', name: 'Default Pipeline' },
      ],
    });

    const { result } = renderHook(() => useSelectedPipeline('project-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasAssignment).toBe(true);
    expect(result.current.pipelineId).toBe('pipeline-1');
    expect(result.current.pipelineName).toBe('Full Review Pipeline');
  });

  it('returns Unknown Pipeline when the assigned id is missing from the list', async () => {
    mockGetAssignment.mockResolvedValue({ project_id: 'project-1', pipeline_id: 'pipeline-9' });
    mockList.mockResolvedValue({
      pipelines: [{ id: 'pipeline-1', name: 'Full Review Pipeline' }],
    });

    const { result } = renderHook(() => useSelectedPipeline('project-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasAssignment).toBe(true);
    expect(result.current.pipelineName).toBe('Unknown Pipeline');
  });

  it('disables queries when projectId is null', () => {
    const { result } = renderHook(() => useSelectedPipeline(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.hasAssignment).toBe(false);
    expect(mockGetAssignment).not.toHaveBeenCalled();
    expect(mockList).not.toHaveBeenCalled();
  });
});
