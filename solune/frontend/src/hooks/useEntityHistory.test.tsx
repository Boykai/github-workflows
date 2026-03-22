import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';

const mockUseInfiniteList = vi.fn();

vi.mock('./useInfiniteList', () => ({
  useInfiniteList: (...args: unknown[]) => mockUseInfiniteList(...args),
}));

vi.mock('@/services/api', () => ({
  activityApi: {
    entityHistory: vi.fn(),
  },
}));

import { useEntityHistory } from './useEntityHistory';
import { activityApi } from '@/services/api';

const mockActivityApi = activityApi as unknown as {
  entityHistory: ReturnType<typeof vi.fn>;
};

const mockEvent = {
  id: 'evt-1',
  event_type: 'issue.updated',
  entity_type: 'issue',
  entity_id: 'issue-1',
  project_id: 'proj-1',
  actor: 'user-1',
  action: 'updated',
  summary: 'Updated an issue',
  created_at: '2024-01-01T00:00:00Z',
};

describe('useEntityHistory', () => {
  beforeEach(() => vi.clearAllMocks());

  it('passes correct options to useInfiniteList on success', () => {
    const fakeReturn = {
      allItems: [mockEvent],
      totalCount: 1,
      isSuccess: true,
      isLoading: false,
    };
    mockUseInfiniteList.mockReturnValue(fakeReturn);

    const { result } = renderHook(() =>
      useEntityHistory('proj-1', 'issue', 'issue-1'),
    );

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['activity', 'entity', 'proj-1', 'issue', 'issue-1'],
        limit: 50,
        staleTime: 30_000,
        enabled: true,
      }),
    );
    expect(result.current).toBe(fakeReturn);

    // Verify the queryFn calls activityApi.entityHistory with correct args
    const opts = mockUseInfiniteList.mock.calls[0][0];
    opts.queryFn({ limit: 50, cursor: 'cursor-abc' });
    expect(mockActivityApi.entityHistory).toHaveBeenCalledWith(
      'proj-1',
      'issue',
      'issue-1',
      { limit: 50, cursor: 'cursor-abc' },
    );
  });

  it('is disabled when projectId is empty', () => {
    mockUseInfiniteList.mockReturnValue({ allItems: [], isLoading: false });

    renderHook(() => useEntityHistory('', 'issue', 'issue-1'));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({ enabled: false }),
    );
  });

  it('is disabled when entityType is empty', () => {
    mockUseInfiniteList.mockReturnValue({ allItems: [], isLoading: false });

    renderHook(() => useEntityHistory('proj-1', '', 'issue-1'));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({ enabled: false }),
    );
  });

  it('is disabled when entityId is empty', () => {
    mockUseInfiniteList.mockReturnValue({ allItems: [], isLoading: false });

    renderHook(() => useEntityHistory('proj-1', 'issue', ''));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({ enabled: false }),
    );
  });

  it('is enabled when all parameters are provided', () => {
    mockUseInfiniteList.mockReturnValue({ allItems: [], isLoading: false });

    renderHook(() => useEntityHistory('proj-1', 'issue', 'issue-1'));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({ enabled: true }),
    );
  });
});
