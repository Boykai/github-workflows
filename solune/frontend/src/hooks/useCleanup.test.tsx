import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

vi.mock('@/services/api', () => ({
  cleanupApi: {
    preflight: vi.fn(),
    execute: vi.fn(),
    history: vi.fn(),
  },
}));

import * as api from '@/services/api';
import { useCleanup } from './useCleanup';

const mockCleanupApi = api.cleanupApi as unknown as {
  preflight: ReturnType<typeof vi.fn>;
  execute: ReturnType<typeof vi.fn>;
  history: ReturnType<typeof vi.fn>;
};

describe('useCleanup', () => {
  beforeEach(() => vi.clearAllMocks());

  it('starts in idle state', () => {
    const { result } = renderHook(() => useCleanup());
    expect(result.current.state).toBe('idle');
    expect(result.current.preflightData).toBeNull();
    expect(result.current.executeResult).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('transitions to confirming after successful preflight', async () => {
    const preflightData = {
      has_permission: true,
      branches: [],
      pull_requests: [],
      issues: [],
    };
    mockCleanupApi.preflight.mockResolvedValue(preflightData);

    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.startPreflight('owner', 'repo', 'proj-1');
    });

    expect(result.current.state).toBe('confirming');
    expect(result.current.preflightData).toEqual(preflightData);
  });

  it('sets permissionError and stays idle when no permission', async () => {
    mockCleanupApi.preflight.mockResolvedValue({
      has_permission: false,
      permission_error: 'No access',
    });

    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.startPreflight('owner', 'repo', 'proj-1');
    });

    expect(result.current.state).toBe('idle');
    expect(result.current.permissionError).toBe('No access');
  });

  it('sets default permission error when none provided', async () => {
    mockCleanupApi.preflight.mockResolvedValue({
      has_permission: false,
    });

    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.startPreflight('owner', 'repo', 'proj-1');
    });

    expect(result.current.permissionError).toContain('push access');
  });

  it('transitions to summary after successful execute', async () => {
    const executeResult = { deleted_branches: 2, closed_prs: 1 };
    mockCleanupApi.execute.mockResolvedValue(executeResult);

    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.confirmExecute('owner', 'repo', 'proj-1', {
        branches_to_delete: ['branch-1'],
        prs_to_close: [1],
        issues_to_delete: [],
      });
    });

    expect(result.current.state).toBe('summary');
    expect(result.current.executeResult).toEqual(executeResult);
  });

  it('transitions to summary with error on execute failure', async () => {
    mockCleanupApi.execute.mockRejectedValue(new Error('Execute failed'));

    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.confirmExecute('owner', 'repo', 'proj-1', {
        branches_to_delete: [],
        prs_to_close: [],
        issues_to_delete: [],
      });
    });

    expect(result.current.state).toBe('summary');
    expect(result.current.error).toBe('Execute failed');
  });

  it('cancel resets to idle', async () => {
    mockCleanupApi.preflight.mockResolvedValue({ has_permission: true, branches: [] });
    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.startPreflight('owner', 'repo', 'proj-1');
    });
    expect(result.current.state).toBe('confirming');

    act(() => {
      result.current.cancel();
    });

    expect(result.current.state).toBe('idle');
    expect(result.current.preflightData).toBeNull();
  });

  it('dismiss resets from summary to idle', async () => {
    mockCleanupApi.execute.mockResolvedValue({ deleted_branches: 0 });
    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.confirmExecute('owner', 'repo', 'proj-1', {
        branches_to_delete: [],
        prs_to_close: [],
        issues_to_delete: [],
      });
    });

    act(() => {
      result.current.dismiss();
    });

    expect(result.current.state).toBe('idle');
    expect(result.current.executeResult).toBeNull();
  });

  it('loadHistory fetches audit history', async () => {
    const historyData = { entries: [{ id: '1', action: 'cleanup' }] };
    mockCleanupApi.history.mockResolvedValue(historyData);

    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.loadHistory('owner', 'repo');
    });

    expect(result.current.historyData).toEqual(historyData);
    expect(mockCleanupApi.history).toHaveBeenCalledWith('owner', 'repo');
  });

  it('showAuditHistory / closeAuditHistory toggles state', () => {
    const { result } = renderHook(() => useCleanup());

    act(() => {
      result.current.showAuditHistory();
    });
    expect(result.current.state).toBe('auditHistory');

    act(() => {
      result.current.closeAuditHistory();
    });
    expect(result.current.state).toBe('idle');
    expect(result.current.historyData).toBeNull();
  });

  it('sets error on preflight failure', async () => {
    mockCleanupApi.preflight.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useCleanup());

    await act(async () => {
      await result.current.startPreflight('owner', 'repo', 'proj-1');
    });

    expect(result.current.state).toBe('idle');
    expect(result.current.error).toBe('Network error');
  });
});
