import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  choresApi: {
    list: vi.fn(),
    listPaginated: vi.fn(),
    listTemplates: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    trigger: vi.fn(),
    chat: vi.fn(),
    inlineUpdate: vi.fn(),
    createWithAutoMerge: vi.fn(),
    evaluateTriggers: vi.fn(),
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
}));

import * as api from '@/services/api';
import {
  useChoresListPaginated,
  useChoreTemplates,
  useCreateChore,
  useUpdateChore,
  useDeleteChore,
  useTriggerChore,
  useChoreChat,
} from './useChores';

const mockChoresApi = api.choresApi as unknown as {
  list: ReturnType<typeof vi.fn>;
  listPaginated: ReturnType<typeof vi.fn>;
  listTemplates: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
  trigger: ReturnType<typeof vi.fn>;
  chat: ReturnType<typeof vi.fn>;
  inlineUpdate: ReturnType<typeof vi.fn>;
  createWithAutoMerge: ReturnType<typeof vi.fn>;
  evaluateTriggers: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockChore = {
  id: 'chore-1',
  name: 'Daily standup',
  schedule: '0 9 * * *',
  status: 'active',
};

describe('useChoreTemplates', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns templates list', async () => {
    const templates = [{ id: 'tpl-1', name: 'Bug report' }];
    mockChoresApi.listTemplates.mockResolvedValue(templates);

    const { result } = renderHook(() => useChoreTemplates('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(templates);
  });
});

describe('useCreateChore', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls create API', async () => {
    mockChoresApi.create.mockResolvedValue(mockChore);

    const { result } = renderHook(() => useCreateChore('proj-1'), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ name: 'New Chore' } as never);
    });

    expect(mockChoresApi.create).toHaveBeenCalledWith('proj-1', { name: 'New Chore' });
  });
});

describe('useUpdateChore', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls update API', async () => {
    mockChoresApi.update.mockResolvedValue(mockChore);

    const { result } = renderHook(() => useUpdateChore('proj-1'), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        choreId: 'chore-1',
        data: { status: 'paused' },
      } as never);
    });

    expect(mockChoresApi.update).toHaveBeenCalledWith('proj-1', 'chore-1', { status: 'paused' });
  });
});

describe('useDeleteChore', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls delete API', async () => {
    mockChoresApi.delete.mockResolvedValue({ deleted: true, closed_issue_number: null });

    const { result } = renderHook(() => useDeleteChore('proj-1'), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync('chore-1');
    });

    expect(mockChoresApi.delete).toHaveBeenCalledWith('proj-1', 'chore-1');
  });
});

describe('useTriggerChore', () => {
  beforeEach(() => vi.clearAllMocks());

  it('triggers a chore', async () => {
    mockChoresApi.trigger.mockResolvedValue({ triggered: true, issue_number: 10 });

    const { result } = renderHook(() => useTriggerChore('proj-1'), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ choreId: 'chore-1', parentIssueCount: 5 });
    });

    expect(mockChoresApi.trigger).toHaveBeenCalledWith('proj-1', 'chore-1', 5);
  });
});

describe('useChoreChat', () => {
  beforeEach(() => vi.clearAllMocks());

  it('sends a chat message', async () => {
    const response = { message: 'Got it', actions: [] };
    mockChoresApi.chat.mockResolvedValue(response);

    const { result } = renderHook(() => useChoreChat('proj-1'), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      const res = await result.current.mutateAsync({ content: 'Hello' } as never);
      expect(res).toEqual(response);
    });
  });
});

describe('useChoresListPaginated', () => {
  beforeEach(() => vi.clearAllMocks());

  const mockPaginatedResponse = {
    items: [mockChore],
    has_more: false,
    next_cursor: null,
    total_count: 1,
  };

  it('calls listPaginated with default params', async () => {
    mockChoresApi.listPaginated.mockResolvedValue(mockPaginatedResponse);

    const { result } = renderHook(() => useChoresListPaginated('proj-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.allItems).toHaveLength(1));
    expect(mockChoresApi.listPaginated).toHaveBeenCalledWith('proj-1', {
      limit: 25,
      cursor: undefined,
    });
  });

  it('does not fetch when projectId is null', () => {
    renderHook(() => useChoresListPaginated(null), { wrapper: createWrapper() });
    expect(mockChoresApi.listPaginated).not.toHaveBeenCalled();
  });

  it('includes filter params in API call', async () => {
    mockChoresApi.listPaginated.mockResolvedValue(mockPaginatedResponse);

    const filters = { status: 'active', search: 'deploy', sort: 'name', order: 'asc' };
    const { result } = renderHook(
      () => useChoresListPaginated('proj-1', filters),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.allItems).toHaveLength(1));
    expect(mockChoresApi.listPaginated).toHaveBeenCalledWith('proj-1', {
      limit: 25,
      cursor: undefined,
      ...filters,
    });
  });

  it('produces different query keys for different filter values', async () => {
    const wrapper = createWrapper();

    mockChoresApi.listPaginated.mockResolvedValue(mockPaginatedResponse);

    renderHook(
      () => useChoresListPaginated('proj-1', { status: 'active' }),
      { wrapper },
    );
    renderHook(
      () => useChoresListPaginated('proj-1', { status: 'paused' }),
      { wrapper },
    );

    // Both hooks should call the API — different filter values produce separate caches
    await waitFor(() => expect(mockChoresApi.listPaginated).toHaveBeenCalledTimes(2));
  });

  it('changing filter triggers fresh fetch', async () => {
    mockChoresApi.listPaginated.mockResolvedValue(mockPaginatedResponse);

    let filters = { status: 'active' };
    const { result, rerender } = renderHook(
      () => useChoresListPaginated('proj-1', filters),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.allItems).toHaveLength(1));
    expect(mockChoresApi.listPaginated).toHaveBeenCalledTimes(1);

    // Change filters
    filters = { status: 'paused' };
    rerender();

    await waitFor(() => expect(mockChoresApi.listPaginated).toHaveBeenCalledTimes(2));
  });
});
