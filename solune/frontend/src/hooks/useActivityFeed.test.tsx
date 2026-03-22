import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';

const mockUseInfiniteList = vi.fn();

vi.mock('./useInfiniteList', () => ({
  useInfiniteList: (...args: unknown[]) => mockUseInfiniteList(...args),
}));

vi.mock('@/services/api', () => ({
  activityApi: {
    feed: vi.fn(),
  },
}));

import { useActivityFeed } from './useActivityFeed';
import { activityApi } from '@/services/api';

const mockActivityApi = activityApi as unknown as {
  feed: ReturnType<typeof vi.fn>;
};

const mockEvent = {
  id: 'evt-1',
  event_type: 'issue.created',
  entity_type: 'issue',
  entity_id: 'issue-1',
  project_id: 'proj-1',
  actor: 'user-1',
  action: 'created',
  summary: 'Created an issue',
  created_at: '2024-01-01T00:00:00Z',
};

describe('useActivityFeed', () => {
  beforeEach(() => vi.clearAllMocks());

  it('passes correct options to useInfiniteList on success', () => {
    const fakeReturn = {
      allItems: [mockEvent],
      totalCount: 1,
      isSuccess: true,
      isLoading: false,
    };
    mockUseInfiniteList.mockReturnValue(fakeReturn);

    const { result } = renderHook(() => useActivityFeed('proj-1'));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['activity', 'proj-1', undefined],
        limit: 50,
        staleTime: 30_000,
        enabled: true,
      }),
    );
    expect(result.current).toBe(fakeReturn);

    // Verify the queryFn calls activityApi.feed with correct args
    const opts = mockUseInfiniteList.mock.calls[0][0];
    opts.queryFn({ limit: 50, cursor: 'abc' });
    expect(mockActivityApi.feed).toHaveBeenCalledWith('proj-1', {
      limit: 50,
      cursor: 'abc',
      event_type: undefined,
    });
  });

  it('is disabled when projectId is empty', () => {
    mockUseInfiniteList.mockReturnValue({ allItems: [], isLoading: false });

    renderHook(() => useActivityFeed(''));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: false,
      }),
    );
  });

  it('joins event types into a comma-separated param', () => {
    mockUseInfiniteList.mockReturnValue({ allItems: [], isLoading: false });

    renderHook(() => useActivityFeed('proj-1', ['issue.created', 'pr.merged']));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['activity', 'proj-1', 'issue.created,pr.merged'],
      }),
    );

    // Verify the queryFn passes the joined event type
    const opts = mockUseInfiniteList.mock.calls[0][0];
    opts.queryFn({ limit: 50, cursor: undefined });
    expect(mockActivityApi.feed).toHaveBeenCalledWith('proj-1', {
      limit: 50,
      cursor: undefined,
      event_type: 'issue.created,pr.merged',
    });
  });

  it('treats an empty eventTypes array as undefined', () => {
    mockUseInfiniteList.mockReturnValue({ allItems: [], isLoading: false });

    renderHook(() => useActivityFeed('proj-1', []));

    expect(mockUseInfiniteList).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ['activity', 'proj-1', undefined],
      }),
    );
  });
});
