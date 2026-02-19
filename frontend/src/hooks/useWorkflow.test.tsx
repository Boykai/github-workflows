/**
 * Unit tests for useWorkflow hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWorkflow } from './useWorkflow';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

function jsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: 'OK',
    json: () => Promise.resolve(data),
  };
}

function errorResponse(status: number, body?: { error: string }) {
  return {
    ok: false,
    status,
    statusText: 'Error',
    json: body ? () => Promise.resolve(body) : () => Promise.reject(new Error('no json')),
  };
}

describe('useWorkflow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should initialize with isLoading false and no error', () => {
    const { result } = renderHook(() => useWorkflow());
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  describe('confirmRecommendation', () => {
    it('should return result on success', async () => {
      const workflowResult = { success: true, message: 'Created' };
      mockFetch.mockResolvedValue(jsonResponse(workflowResult));

      const { result } = renderHook(() => useWorkflow());

      let res: unknown;
      await act(async () => {
        res = await result.current.confirmRecommendation('rec-1');
      });

      expect(res).toEqual(workflowResult);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/workflow/recommendations/rec-1/confirm'),
        expect.objectContaining({ method: 'POST', credentials: 'include' })
      );
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should set error on failure', async () => {
      mockFetch.mockResolvedValue(errorResponse(400, { error: 'Bad request' }));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        try {
          await result.current.confirmRecommendation('rec-1');
        } catch {
          // expected
        }
      });

      expect(result.current.error).toBe('Bad request');
      expect(result.current.isLoading).toBe(false);
    });

    it('should set loading state during request', async () => {
      let resolvePromise: (val: unknown) => void;
      mockFetch.mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      const { result } = renderHook(() => useWorkflow());

      let confirmPromise: Promise<unknown>;
      act(() => {
        confirmPromise = result.current.confirmRecommendation('rec-1');
      });

      // Loading should be true while in flight
      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolvePromise!(jsonResponse({ success: true, message: 'ok' }));
        await confirmPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('rejectRecommendation', () => {
    it('should resolve on success', async () => {
      mockFetch.mockResolvedValue(jsonResponse({}));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        await result.current.rejectRecommendation('rec-1');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/workflow/recommendations/rec-1/reject'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.current.error).toBeNull();
    });

    it('should set error on failure', async () => {
      mockFetch.mockResolvedValue(errorResponse(500, { error: 'Server error' }));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        try {
          await result.current.rejectRecommendation('rec-1');
        } catch {
          // expected
        }
      });

      expect(result.current.error).toBe('Server error');
    });
  });

  describe('getConfig', () => {
    it('should return config on success', async () => {
      const config = { project_id: 'PVT_1', enabled: true };
      mockFetch.mockResolvedValue(jsonResponse(config));

      const { result } = renderHook(() => useWorkflow());

      let res: unknown;
      await act(async () => {
        res = await result.current.getConfig();
      });

      expect(res).toEqual(config);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/workflow/config'),
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('should set error on failure', async () => {
      mockFetch.mockResolvedValue(errorResponse(403, { error: 'Forbidden' }));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        try {
          await result.current.getConfig();
        } catch {
          // expected
        }
      });

      expect(result.current.error).toBe('Forbidden');
    });
  });

  describe('updateConfig', () => {
    it('should return updated config on success', async () => {
      const config = { project_id: 'PVT_1', enabled: false };
      mockFetch.mockResolvedValue(jsonResponse(config));

      const { result } = renderHook(() => useWorkflow());

      let res: unknown;
      await act(async () => {
        res = await result.current.updateConfig({ enabled: false });
      });

      expect(res).toEqual(config);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/workflow/config'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ enabled: false }),
        })
      );
    });

    it('should set error on failure', async () => {
      mockFetch.mockResolvedValue(errorResponse(422, { error: 'Invalid config' }));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        try {
          await result.current.updateConfig({ enabled: true });
        } catch {
          // expected
        }
      });

      expect(result.current.error).toBe('Invalid config');
    });
  });

  describe('network errors', () => {
    it('should handle fetch rejection', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        try {
          await result.current.confirmRecommendation('rec-1');
        } catch {
          // expected
        }
      });

      expect(result.current.error).toBe('Network error');
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle non-Error throw in catch', async () => {
      mockFetch.mockResolvedValue(errorResponse(500));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        try {
          await result.current.getConfig();
        } catch {
          // expected
        }
      });

      // Falls back to error message from status code
      expect(result.current.error).toContain('Failed to get config: 500');
    });
  });

  describe('error state reset', () => {
    it('should clear error on new request', async () => {
      // First call fails
      mockFetch.mockResolvedValueOnce(errorResponse(500, { error: 'Fail' }));

      const { result } = renderHook(() => useWorkflow());

      await act(async () => {
        try {
          await result.current.getConfig();
        } catch {
          // expected
        }
      });

      expect(result.current.error).toBe('Fail');

      // Second call succeeds
      mockFetch.mockResolvedValueOnce(jsonResponse({ project_id: 'PVT_1' }));

      await act(async () => {
        await result.current.getConfig();
      });

      expect(result.current.error).toBeNull();
    });
  });
});
