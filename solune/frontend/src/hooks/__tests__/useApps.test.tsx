import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { appKeys, useApps, useApp, useCreateApp, useDeleteApp, useStartApp, useStopApp } from '../useApps';
import type { App, AppStatusResponse } from '@/types/apps';

const mocks = vi.hoisted(() => ({
  apiList: vi.fn(),
  apiGet: vi.fn(),
  apiCreate: vi.fn(),
  apiDelete: vi.fn(),
  apiStart: vi.fn(),
  apiStop: vi.fn(),
}));

vi.mock('@/services/api', () => ({
  appsApi: {
    list: mocks.apiList,
    get: mocks.apiGet,
    create: mocks.apiCreate,
    delete: mocks.apiDelete,
    start: mocks.apiStart,
    stop: mocks.apiStop,
  },
  ApiError: class ApiError extends Error {
    status: number;
    error: { error: string };
    constructor(status: number, error: { error: string }) {
      super(error.error);
      this.status = status;
      this.error = error;
    }
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

function createApp(overrides: Partial<App> = {}): App {
  return {
    name: 'my-app',
    display_name: 'My App',
    description: 'Test app',
    directory_path: '/apps/my-app',
    associated_pipeline_id: null,
    status: 'stopped',
    repo_type: 'same-repo',
    external_repo_url: null,
    port: null,
    error_message: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('appKeys', () => {
  it('returns the correct key structure', () => {
    expect(appKeys.all).toEqual(['apps']);
    expect(appKeys.list()).toEqual(['apps', 'list']);
    expect(appKeys.detail('my-app')).toEqual(['apps', 'detail', 'my-app']);
    expect(appKeys.status('my-app')).toEqual(['apps', 'status', 'my-app']);
  });
});

describe('useApps', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns apps data on success', async () => {
    const apps = [createApp()];
    mocks.apiList.mockResolvedValue(apps);

    const { result } = renderHook(() => useApps(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(apps);
    expect(result.current.error).toBeNull();
  });

  it('exposes error when the API call fails', async () => {
    const error = new Error('Network error');
    mocks.apiList.mockRejectedValue(error);

    const { result } = renderHook(() => useApps(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
    });

    expect(result.current.data).toBeUndefined();
  });
});

describe('useApp', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns a single app on success', async () => {
    const app = createApp();
    mocks.apiGet.mockResolvedValue(app);

    const { result } = renderHook(() => useApp('my-app'), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(app);
  });

  it('does not fetch when name is undefined', () => {
    const { result } = renderHook(() => useApp(undefined), { wrapper: createWrapper() });

    expect(result.current.isLoading).toBe(false);
    expect(mocks.apiGet).not.toHaveBeenCalled();
  });
});

describe('useCreateApp', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls appsApi.create and returns the created app', async () => {
    const app = createApp();
    mocks.apiCreate.mockResolvedValue(app);

    const { result } = renderHook(() => useCreateApp(), { wrapper: createWrapper() });

    result.current.mutate({ name: 'my-app', display_name: 'My App', branch: 'main' });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mocks.apiCreate).toHaveBeenCalledWith({
      name: 'my-app',
      display_name: 'My App',
      branch: 'main',
    });
  });

  it('surfaces error on API failure', async () => {
    const error = new Error('Create failed');
    mocks.apiCreate.mockRejectedValue(error);

    const { result } = renderHook(() => useCreateApp(), { wrapper: createWrapper() });

    result.current.mutate({ name: 'bad-app', display_name: 'Bad App', branch: 'main' });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBe(error);
  });
});

describe('useDeleteApp', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls appsApi.delete with the app name', async () => {
    mocks.apiDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteApp(), { wrapper: createWrapper() });

    result.current.mutate('my-app');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mocks.apiDelete).toHaveBeenCalledWith('my-app');
  });
});

describe('useStartApp', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls appsApi.start and returns status response', async () => {
    const status: AppStatusResponse = {
      name: 'my-app',
      status: 'active',
      port: 3000,
      error_message: null,
    };
    mocks.apiStart.mockResolvedValue(status);

    const { result } = renderHook(() => useStartApp(), { wrapper: createWrapper() });

    result.current.mutate('my-app');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mocks.apiStart).toHaveBeenCalledWith('my-app');
  });
});

describe('useStopApp', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls appsApi.stop and returns status response', async () => {
    const status: AppStatusResponse = {
      name: 'my-app',
      status: 'stopped',
      port: null,
      error_message: null,
    };
    mocks.apiStop.mockResolvedValue(status);

    const { result } = renderHook(() => useStopApp(), { wrapper: createWrapper() });

    result.current.mutate('my-app');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mocks.apiStop).toHaveBeenCalledWith('my-app');
  });
});
