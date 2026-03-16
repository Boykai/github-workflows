import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useEvaluateChoresTriggers, choreKeys } from './useChores';

const mockEvaluateTriggers = vi.fn();

vi.mock('@/services/api', () => ({
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error: { error: string }
    ) {
      super(error.error);
      this.name = 'ApiError';
    }
  },
  choresApi: {
    evaluateTriggers: (...args: unknown[]) => mockEvaluateTriggers(...args),
  },
}));

function createWrapper(queryClient?: QueryClient) {
  const client =
    queryClient ??
    new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

async function flushEffect() {
  await act(async () => {
    await Promise.resolve();
  });
}

describe('useEvaluateChoresTriggers', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    mockEvaluateTriggers.mockResolvedValue({ triggered: 0 });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('does not poll until both a project and board data are available', () => {
    renderHook(() => useEvaluateChoresTriggers(null, 3, true), {
      wrapper: createWrapper(),
    });
    renderHook(() => useEvaluateChoresTriggers('PVT_1', 3, false), {
      wrapper: createWrapper(),
    });

    act(() => {
      vi.advanceTimersByTime(60_000);
    });

    expect(mockEvaluateTriggers).not.toHaveBeenCalled();
  });

  it('runs immediately, keeps polling, and invalidates the chores list when triggers fire', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();
    mockEvaluateTriggers.mockResolvedValue({ triggered: 2 });

    renderHook(() => useEvaluateChoresTriggers('PVT_1', 5, true), {
      wrapper: createWrapper(queryClient),
    });

    await flushEffect();

    expect(mockEvaluateTriggers).toHaveBeenCalledWith('PVT_1', 5);
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: choreKeys.list('PVT_1') });

    await act(async () => {
      vi.advanceTimersByTime(60_000);
    });

    await flushEffect();

    expect(mockEvaluateTriggers).toHaveBeenCalledTimes(2);
  });

  it('skips invalidation when the evaluation reports no triggered chores', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    renderHook(() => useEvaluateChoresTriggers('PVT_1', 1, true), {
      wrapper: createWrapper(queryClient),
    });

    await flushEffect();

    expect(mockEvaluateTriggers).toHaveBeenCalledWith('PVT_1', 1);
    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});
