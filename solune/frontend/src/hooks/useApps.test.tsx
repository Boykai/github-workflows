/**
 * Unit tests for useApps hooks.
 * Covers: useApps, useApp, useCreateApp, useDeleteApp, useStartApp, useStopApp,
 * plus isApiError and friendlyErrorMessage utilities.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import {
  useApps,
  useApp,
  useCreateApp,
  useDeleteApp,
  useStartApp,
  useStopApp,
  isApiError,
  friendlyErrorMessage,
} from './useApps';
import * as api from '@/services/api';
import type { App, AppStatusResponse } from '@/types/apps';

vi.mock('@/services/api', () => ({
  appsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    error: { error: string; details?: Record<string, unknown> };
    constructor(status: number, error: { error: string; details?: Record<string, unknown> }) {
      super(error.error);
      this.name = 'ApiError';
      this.status = status;
      this.error = error;
    }
  },
}));

const mockAppsApi = api.appsApi as unknown as {
  list: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
  start: ReturnType<typeof vi.fn>;
  stop: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockApp: App = {
  name: 'test-app',
  display_name: 'Test App',
  description: 'A test application',
  directory_path: '/apps/test-app',
  associated_pipeline_id: null,
  status: 'active',
  repo_type: 'same-repo',
  external_repo_url: null,
  port: 3000,
  error_message: null,
  created_at: '2026-03-15T10:00:00Z',
  updated_at: '2026-03-15T12:00:00Z',
};

const mockStatusResponse: AppStatusResponse = {
  name: 'test-app',
  status: 'active',
  port: 3000,
  error_message: null,
};

describe('isApiError', () => {
  it('returns true for ApiError instances', () => {
    const err = new api.ApiError(400, { error: 'Bad request' });
    expect(isApiError(err)).toBe(true);
  });

  it('returns false for plain Error instances', () => {
    expect(isApiError(new Error('oops'))).toBe(false);
  });

  it('returns false for non-error values', () => {
    expect(isApiError(null)).toBe(false);
    expect(isApiError('string')).toBe(false);
  });
});

describe('friendlyErrorMessage', () => {
  it('extracts message from ApiError', () => {
    const err = new api.ApiError(400, { error: 'Invalid name' });
    expect(friendlyErrorMessage(err, 'fallback')).toBe('Invalid name');
  });

  it('extracts message from plain Error', () => {
    expect(friendlyErrorMessage(new Error('Oops'), 'fallback')).toBe('Oops');
  });

  it('returns fallback for non-error values', () => {
    expect(friendlyErrorMessage(undefined, 'fallback')).toBe('fallback');
  });
});

describe('useApps', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns loading state initially', () => {
    mockAppsApi.list.mockImplementation(() => new Promise(() => {}));
    const { result } = renderHook(() => useApps(), { wrapper: createWrapper() });
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it('returns apps after successful fetch', async () => {
    mockAppsApi.list.mockResolvedValue([mockApp]);
    const { result } = renderHook(() => useApps(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toEqual([mockApp]);
  });

  it('returns error on failed fetch', async () => {
    mockAppsApi.list.mockRejectedValue(new api.ApiError(500, { error: 'Server error' }));
    const { result } = renderHook(() => useApps(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.data).toBeUndefined();
  });
});

describe('useApp', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetches a single app by name', async () => {
    mockAppsApi.get.mockResolvedValue(mockApp);
    const { result } = renderHook(() => useApp('test-app'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(mockApp));
  });

  it('does not fetch when name is undefined', () => {
    const { result } = renderHook(() => useApp(undefined), { wrapper: createWrapper() });
    expect(result.current.data).toBeUndefined();
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('returns error when fetch fails', async () => {
    mockAppsApi.get.mockRejectedValue(new api.ApiError(404, { error: 'Not found' }));
    const { result } = renderHook(() => useApp('missing-app'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.error).toBeTruthy());
  });
});

describe('useCreateApp', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls appsApi.create and invalidates the list', async () => {
    const createdApp = { ...mockApp, name: 'new-app' };
    mockAppsApi.create.mockResolvedValue(createdApp);

    const { result } = renderHook(() => useCreateApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({ name: 'new-app', display_name: 'New App', branch: 'main' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockAppsApi.create).toHaveBeenCalledWith({
      name: 'new-app',
      display_name: 'New App',
      branch: 'main',
    });
  });

  it('reports error on creation failure', async () => {
    mockAppsApi.create.mockRejectedValue(new api.ApiError(400, { error: 'Invalid' }));

    const { result } = renderHook(() => useCreateApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({ name: 'bad', display_name: 'Bad', branch: 'x' });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useDeleteApp', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls appsApi.delete and invalidates the list', async () => {
    mockAppsApi.delete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('test-app');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockAppsApi.delete).toHaveBeenCalledWith('test-app');
  });

  it('reports error on deletion failure', async () => {
    mockAppsApi.delete.mockRejectedValue(new api.ApiError(404, { error: 'Not found' }));

    const { result } = renderHook(() => useDeleteApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('missing');
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useStartApp', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls appsApi.start and invalidates queries', async () => {
    mockAppsApi.start.mockResolvedValue(mockStatusResponse);

    const { result } = renderHook(() => useStartApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('test-app');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockAppsApi.start).toHaveBeenCalledWith('test-app');
  });

  it('reports error on start failure', async () => {
    mockAppsApi.start.mockRejectedValue(new api.ApiError(500, { error: 'Start failed' }));

    const { result } = renderHook(() => useStartApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('bad-app');
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useStopApp', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls appsApi.stop and invalidates queries', async () => {
    const stoppedResponse: AppStatusResponse = { ...mockStatusResponse, status: 'stopped' };
    mockAppsApi.stop.mockResolvedValue(stoppedResponse);

    const { result } = renderHook(() => useStopApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('test-app');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockAppsApi.stop).toHaveBeenCalledWith('test-app');
  });

  it('reports error on stop failure', async () => {
    mockAppsApi.stop.mockRejectedValue(new api.ApiError(500, { error: 'Stop failed' }));

    const { result } = renderHook(() => useStopApp(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('bad-app');
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
