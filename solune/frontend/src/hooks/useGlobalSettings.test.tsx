/**
 * Unit tests for useGlobalSettings hook.
 *
 * Tests query behaviour, mutation flow, cache invalidation, and error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useGlobalSettings } from './useSettings';
import * as api from '@/services/api';
import type { ReactNode } from 'react';
import type { GlobalSettings, GlobalSettingsUpdate } from '@/types';

vi.mock('@/services/api', () => ({
  settingsApi: {
    getGlobalSettings: vi.fn(),
    updateGlobalSettings: vi.fn(),
  },
  signalApi: {},
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error: { error: string; details?: Record<string, unknown> }
    ) {
      super(error.error);
      this.name = 'ApiError';
    }
  },
}));

const mockSettingsApi = api.settingsApi as unknown as {
  getGlobalSettings: ReturnType<typeof vi.fn>;
  updateGlobalSettings: ReturnType<typeof vi.fn>;
};

const sampleSettings: GlobalSettings = {
  ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
  display: { theme: 'dark', default_view: 'chat', sidebar_collapsed: false },
  workflow: {
    default_repository: null,
    default_assignee: '',
    copilot_polling_interval: 60,
  },
  notifications: {
    task_status_change: true,
    agent_completion: true,
    new_recommendation: true,
    chat_mention: true,
  },
  allowed_models: ['gpt-4o'],
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useGlobalSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches global settings on mount', async () => {
    mockSettingsApi.getGlobalSettings.mockResolvedValue(sampleSettings);

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.settings).toEqual(sampleSettings);
    expect(result.current.error).toBeNull();
    expect(mockSettingsApi.getGlobalSettings).toHaveBeenCalledTimes(1);
  });

  it('returns error when fetch fails', async () => {
    mockSettingsApi.getGlobalSettings.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.rawError).toBeTruthy();
    expect(result.current.settings).toBeUndefined();
  });

  it('exposes rawError from query error', async () => {
    const networkError = new Error('Network error');
    mockSettingsApi.getGlobalSettings.mockRejectedValue(networkError);

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.rawError).toBeTruthy();
    });

    expect(result.current.isRateLimitError).toBe(false);
  });

  it('detects rate limit errors', async () => {
    const rateLimitError = new api.ApiError(429, {
      error: 'Rate limited',
    });
    mockSettingsApi.getGlobalSettings.mockRejectedValue(rateLimitError);

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.rawError).toBeTruthy();
    });

    expect(result.current.isRateLimitError).toBe(true);
  });

  it('updates settings via mutation', async () => {
    mockSettingsApi.getGlobalSettings.mockResolvedValue(sampleSettings);
    const updatedSettings = { ...sampleSettings, ai: { ...sampleSettings.ai, model: 'gpt-3.5' } };
    mockSettingsApi.updateGlobalSettings.mockResolvedValue(updatedSettings);

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const update: GlobalSettingsUpdate = {
      ai: { provider: 'copilot', model: 'gpt-3.5', temperature: 0.7 },
    };

    await result.current.updateSettings(update);

    expect(mockSettingsApi.updateGlobalSettings).toHaveBeenCalledWith(update);
  });

  it('exposes refetch function', async () => {
    mockSettingsApi.getGlobalSettings.mockResolvedValue(sampleSettings);

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(typeof result.current.refetch).toBe('function');
  });
});
