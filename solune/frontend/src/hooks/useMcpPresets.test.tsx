import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  toolsApi: {
    listPresets: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, error: { error: string }) {
      super(error.error);
      this.status = status;
      this.name = 'ApiError';
    }
  },
}));

import * as api from '@/services/api';
import { useMcpPresets, mcpPresetKeys } from './useMcpPresets';

const mockToolsApi = api.toolsApi as unknown as {
  listPresets: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockPresets = [
  { id: 'preset-1', name: 'GitHub MCP', description: 'GitHub tools' },
  { id: 'preset-2', name: 'Slack MCP', description: 'Slack tools' },
];

describe('useMcpPresets', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns presets on success', async () => {
    mockToolsApi.listPresets.mockResolvedValue({ presets: mockPresets });

    const { result } = renderHook(() => useMcpPresets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.presets).toEqual(mockPresets);
    expect(result.current.error).toBeNull();
  });

  it('returns empty presets when API returns empty list', async () => {
    mockToolsApi.listPresets.mockResolvedValue({ presets: [] });

    const { result } = renderHook(() => useMcpPresets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.presets).toEqual([]);
  });

  it('exposes error message on failure', async () => {
    mockToolsApi.listPresets.mockRejectedValue(
      new api.ApiError(500, { error: 'Server error' }),
    );

    const { result } = renderHook(() => useMcpPresets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.error).toBe('Server error');
  });

  it('exposes rawError on failure', async () => {
    const err = new api.ApiError(500, { error: 'Server error' });
    mockToolsApi.listPresets.mockRejectedValue(err);

    const { result } = renderHook(() => useMcpPresets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.rawError).toBeTruthy());
    expect(result.current.rawError).toBeInstanceOf(api.ApiError);
  });

  it('returns empty presets before data loads', () => {
    mockToolsApi.listPresets.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useMcpPresets(), {
      wrapper: createWrapper(),
    });

    expect(result.current.presets).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it('has correct query keys', () => {
    expect(mcpPresetKeys.all).toEqual(['mcp-presets']);
  });

  it('exposes refetch function', async () => {
    mockToolsApi.listPresets.mockResolvedValue({ presets: mockPresets });

    const { result } = renderHook(() => useMcpPresets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(typeof result.current.refetch).toBe('function');
  });
});
