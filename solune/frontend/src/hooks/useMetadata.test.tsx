import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';

vi.mock('@/services/api', () => ({
  metadataApi: {
    getMetadata: vi.fn(),
    refreshMetadata: vi.fn(),
  },
}));

import * as api from '@/services/api';
import { useMetadata } from './useMetadata';

const mockMetadataApi = api.metadataApi as unknown as {
  getMetadata: ReturnType<typeof vi.fn>;
  refreshMetadata: ReturnType<typeof vi.fn>;
};

const mockMetadata = {
  labels: [{ id: '1', name: 'bug', color: 'fc2929' }],
  branches: ['main', 'develop'],
  milestones: [{ id: '1', title: 'v1.0' }],
  collaborators: [{ login: 'octocat', avatar_url: 'https://avatar.example.com' }],
};

describe('useMetadata', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns metadata on success', async () => {
    mockMetadataApi.getMetadata.mockResolvedValue(mockMetadata);

    const { result } = renderHook(() => useMetadata('test-org', 'test-repo'));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.metadata).toEqual(mockMetadata);
    expect(result.current.error).toBeNull();
  });

  it('does not fetch when owner is null', () => {
    renderHook(() => useMetadata(null, 'test-repo'));
    expect(mockMetadataApi.getMetadata).not.toHaveBeenCalled();
  });

  it('does not fetch when repo is null', () => {
    renderHook(() => useMetadata('test-org', null));
    expect(mockMetadataApi.getMetadata).not.toHaveBeenCalled();
  });

  it('returns error on failure', async () => {
    mockMetadataApi.getMetadata.mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useMetadata('test-org', 'test-repo'));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('Not found');
    expect(result.current.metadata).toBeNull();
  });

  it('returns error message for non-Error thrown values', async () => {
    mockMetadataApi.getMetadata.mockRejectedValue('string error');

    const { result } = renderHook(() => useMetadata('test-org', 'test-repo'));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('Failed to fetch metadata');
  });

  it('exposes refresh function', async () => {
    mockMetadataApi.getMetadata.mockResolvedValue(mockMetadata);
    const refreshedMetadata = { ...mockMetadata, branches: ['main', 'develop', 'feature'] };
    mockMetadataApi.refreshMetadata.mockResolvedValue(refreshedMetadata);

    const { result } = renderHook(() => useMetadata('test-org', 'test-repo'));

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockMetadataApi.refreshMetadata).toHaveBeenCalledWith('test-org', 'test-repo');
    expect(result.current.metadata).toEqual(refreshedMetadata);
  });

  it('sets loading true during fetch', async () => {
    let resolveFetch: (v: unknown) => void;
    mockMetadataApi.getMetadata.mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve;
      })
    );

    const { result } = renderHook(() => useMetadata('test-org', 'test-repo'));
    expect(result.current.loading).toBe(true);

    await act(async () => {
      resolveFetch!(mockMetadata);
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
  });
});
