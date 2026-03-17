import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  settingsApi: {
    getUserSettings: vi.fn(),
    updateUserSettings: vi.fn(),
    getGlobalSettings: vi.fn(),
    updateGlobalSettings: vi.fn(),
    getProjectSettings: vi.fn(),
    updateProjectSettings: vi.fn(),
    fetchModels: vi.fn(),
  },
  signalApi: {
    getConnection: vi.fn(),
    initiateLink: vi.fn(),
    checkLinkStatus: vi.fn(),
    disconnect: vi.fn(),
    getPreferences: vi.fn(),
    updatePreferences: vi.fn(),
    getBanners: vi.fn(),
    dismissBanner: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error: { error: string }
    ) {
      super(error.error);
    }
  },
}));

vi.mock('@/constants', () => ({
  STALE_TIME_LONG: 0,
  STALE_TIME_SHORT: 0,
}));

import * as api from '@/services/api';
import { useUserSettings, useGlobalSettings, useProjectSettings } from './useSettings';

const mockSettingsApi = api.settingsApi as unknown as {
  getUserSettings: ReturnType<typeof vi.fn>;
  updateUserSettings: ReturnType<typeof vi.fn>;
  getGlobalSettings: ReturnType<typeof vi.fn>;
  updateGlobalSettings: ReturnType<typeof vi.fn>;
  getProjectSettings: ReturnType<typeof vi.fn>;
  updateProjectSettings: ReturnType<typeof vi.fn>;
  fetchModels: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockUserSettings = {
  ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7, agent_model: 'gpt-4o' },
  display: { theme: 'dark', default_view: 'chat', sidebar_collapsed: false },
  workflow: { default_repository: null, default_assignee: '', copilot_polling_interval: 30 },
  notifications: {
    task_status_change: true,
    agent_completion: true,
    new_recommendation: false,
    chat_mention: true,
  },
};

const mockGlobalSettings = {
  ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.5, agent_model: 'gpt-4o' },
  display: { theme: 'light', default_view: 'board', sidebar_collapsed: false },
};

describe('useUserSettings', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns user settings on success', async () => {
    mockSettingsApi.getUserSettings.mockResolvedValue(mockUserSettings);

    const { result } = renderHook(() => useUserSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.settings).toEqual(mockUserSettings);
  });

  it('exposes updateSettings mutation', async () => {
    mockSettingsApi.getUserSettings.mockResolvedValue(mockUserSettings);
    const updatedSettings = { ...mockUserSettings, display: { ...mockUserSettings.display, theme: 'light' } };
    mockSettingsApi.updateUserSettings.mockResolvedValue(updatedSettings);

    const { result } = renderHook(() => useUserSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.settings).toBeDefined());

    await act(async () => {
      await result.current.updateSettings({ display: { theme: 'light' } } as never);
    });

    expect(mockSettingsApi.updateUserSettings).toHaveBeenCalledWith({ display: { theme: 'light' } });
  });

  it('returns error on failure', async () => {
    mockSettingsApi.getUserSettings.mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() => useUserSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBeTruthy();
  });
});

describe('useGlobalSettings', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns global settings on success', async () => {
    mockSettingsApi.getGlobalSettings.mockResolvedValue(mockGlobalSettings);

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.settings).toEqual(mockGlobalSettings);
  });

  it('updates global settings', async () => {
    mockSettingsApi.getGlobalSettings.mockResolvedValue(mockGlobalSettings);
    mockSettingsApi.updateGlobalSettings.mockResolvedValue(mockGlobalSettings);

    const { result } = renderHook(() => useGlobalSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.settings).toBeDefined());

    await act(async () => {
      await result.current.updateSettings({ ai: { temperature: 0.9 } } as never);
    });

    expect(mockSettingsApi.updateGlobalSettings).toHaveBeenCalled();
  });
});

describe('useProjectSettings', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns project settings when projectId is provided', async () => {
    const projectSettings = { ...mockUserSettings, project_id: 'proj-1' };
    mockSettingsApi.getProjectSettings.mockResolvedValue(projectSettings);

    const { result } = renderHook(() => useProjectSettings('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.settings).toEqual(projectSettings);
  });

  it('does not fetch when projectId is undefined', () => {
    renderHook(() => useProjectSettings(undefined), {
      wrapper: createWrapper(),
    });
    expect(mockSettingsApi.getProjectSettings).not.toHaveBeenCalled();
  });
});
