import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

vi.mock('@/services/api', () => ({
  pipelinesApi: {
    list: vi.fn(),
  },
}));

import * as api from '@/services/api';
import { useMentionAutocomplete, MENTION_TOKEN_BASE, MENTION_TOKEN_VALID, MENTION_TOKEN_INVALID } from './useMentionAutocomplete';

const mockPipelinesApi = api.pipelinesApi as unknown as {
  list: ReturnType<typeof vi.fn>;
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const mockPipelines = [
  { id: 'pipe-1', name: 'Build Pipeline' },
  { id: 'pipe-2', name: 'Deploy Pipeline' },
  { id: 'pipe-3', name: 'Test Runner' },
];

function createInputRef() {
  return {
    current: {
      insertTokenAtCursor: vi.fn(),
      focus: vi.fn(),
      getElement: vi.fn(() => null),
      getPlainText: vi.fn(() => 'hello world'),
      clear: vi.fn(),
    },
  };
}

describe('useMentionAutocomplete', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPipelinesApi.list.mockResolvedValue({ pipelines: mockPipelines });
  });

  it('starts with autocomplete closed', () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    expect(result.current.isAutocompleteOpen).toBe(false);
    expect(result.current.filteredPipelines).toEqual([]);
    expect(result.current.highlightedIndex).toBe(0);
  });

  it('opens autocomplete on mention trigger after debounce', async () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.handleMentionTrigger('', 0);
    });

    // Wait for the 150ms debounce to complete
    await waitFor(() => expect(result.current.isAutocompleteOpen).toBe(true));
  });

  it('filters pipelines by query', async () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.handleMentionTrigger('build', 0);
    });

    await waitFor(() => expect(result.current.filteredPipelines.length).toBeGreaterThan(0));
    expect(result.current.filteredPipelines[0].pipeline.name).toBe('Build Pipeline');
  });

  it('dismisses autocomplete', async () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.handleMentionTrigger('', 0);
    });
    await waitFor(() => expect(result.current.isAutocompleteOpen).toBe(true));

    act(() => {
      result.current.handleMentionDismiss();
    });
    expect(result.current.isAutocompleteOpen).toBe(false);
  });

  it('selects a pipeline and adds a token', async () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.handleMentionTrigger('', 0);
    });
    await waitFor(() => expect(result.current.isAutocompleteOpen).toBe(true));

    act(() => {
      result.current.handleSelect({ id: 'pipe-1', name: 'Build Pipeline' } as never);
    });

    expect(result.current.mentionTokens).toHaveLength(1);
    expect(result.current.mentionTokens[0].pipelineId).toBe('pipe-1');
    expect(result.current.isAutocompleteOpen).toBe(false);
    expect(result.current.activePipelineId).toBe('pipe-1');
  });

  it('removes a token', async () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.handleSelect({ id: 'pipe-1', name: 'Build Pipeline' } as never);
    });
    expect(result.current.mentionTokens).toHaveLength(1);

    act(() => {
      result.current.handleTokenRemove('pipe-1');
    });
    expect(result.current.mentionTokens).toHaveLength(0);
    expect(result.current.activePipelineId).toBeNull();
  });

  it('getPlainTextContent delegates to inputRef', () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    expect(result.current.getPlainTextContent()).toBe('hello world');
  });

  it('reset clears tokens and calls inputRef.clear', () => {
    const inputRef = createInputRef();
    const { result } = renderHook(
      () => useMentionAutocomplete({ projectId: 'proj-1', inputRef: inputRef as never }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.handleSelect({ id: 'pipe-1', name: 'Build Pipeline' } as never);
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.mentionTokens).toHaveLength(0);
    expect(inputRef.current.clear).toHaveBeenCalled();
  });

  it('exports correct CSS token class constants', () => {
    expect(MENTION_TOKEN_BASE).toContain('inline-flex');
    expect(MENTION_TOKEN_VALID).toContain('bg-blue-100');
    expect(MENTION_TOKEN_INVALID).toContain('bg-red-100');
  });
});
