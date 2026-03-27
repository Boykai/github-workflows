import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useBoardProjection, type BoardProjectionConfig } from './useBoardProjection';
import type { BoardDataResponse, BoardColumn } from '@/types';

// ── Test Data Factories ──

function createBoardColumn(
  name: string,
  itemCount: number,
  overrides: Partial<BoardColumn> = {},
): BoardColumn {
  return {
    status: {
      option_id: `opt-${name}`,
      name,
      color: 'GRAY',
    },
    items: Array.from({ length: itemCount }, (_, i) => ({
      task_id: `task-${name}-${i}`,
      project_id: 'proj-1',
      github_item_id: `item-${name}-${i}`,
      title: `Task ${name} ${i}`,
      status: name,
      status_option_id: `opt-${name}`,
      assignees: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })),
    item_count: itemCount,
    estimate_total: 0,
    ...overrides,
  };
}

function createBoardData(columns: BoardColumn[]): BoardDataResponse {
  return {
    project: {
      project_id: 'proj-1',
      name: 'Test Project',
      url: 'https://example.com',
      owner_login: 'testuser',
      type: 'user',
      item_count: columns.reduce((sum, col) => sum + col.items.length, 0),
      status_field: {
        field_id: 'field-1',
        options: columns.map((c) => c.status),
      },
    },
    columns,
  };
}

// ── Mock IntersectionObserver ──

class MockIntersectionObserver {
  callback: IntersectionObserverCallback;
  options: IntersectionObserverInit | undefined;
  elements: Element[] = [];

  constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    this.callback = callback;
    this.options = options;
  }

  observe(element: Element) {
    this.elements.push(element);
  }

  unobserve(element: Element) {
    this.elements = this.elements.filter((el) => el !== element);
  }

  disconnect() {
    this.elements = [];
  }
}

// ── Tests ──

describe('useBoardProjection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);
    vi.stubGlobal('requestAnimationFrame', (cb: () => void) => {
      cb();
      return 0;
    });
    vi.stubGlobal('cancelAnimationFrame', vi.fn());
  });

  // ── Null Board Data ──

  it('returns empty projections for null board data', () => {
    const { result } = renderHook(() => useBoardProjection(null));

    expect(result.current.columnProjections.size).toBe(0);
    expect(result.current.totalRenderedItems).toBe(0);
    expect(result.current.totalDatasetItems).toBe(0);
    expect(result.current.isInitialRenderComplete).toBe(false);
  });

  // ── Basic Projection ──

  it('computes projections for columns within buffer size', () => {
    const boardData = createBoardData([
      createBoardColumn('Todo', 5),
      createBoardColumn('Done', 3),
    ]);

    const { result } = renderHook(() =>
      useBoardProjection(boardData, { bufferSize: 10 }),
    );

    // Both columns fit within buffer
    const todoProjn = result.current.columnProjections.get('Todo');
    expect(todoProjn).toBeDefined();
    expect(todoProjn!.renderedRange).toEqual({ start: 0, end: 5 });
    expect(todoProjn!.totalItems).toBe(5);
    expect(todoProjn!.hasMore).toBe(false);

    const doneProjn = result.current.columnProjections.get('Done');
    expect(doneProjn).toBeDefined();
    expect(doneProjn!.renderedRange).toEqual({ start: 0, end: 3 });
    expect(doneProjn!.totalItems).toBe(3);
    expect(doneProjn!.hasMore).toBe(false);
  });

  it('limits rendered items to buffer size for large columns', () => {
    const boardData = createBoardData([
      createBoardColumn('Todo', 50),
    ]);

    const { result } = renderHook(() =>
      useBoardProjection(boardData, { bufferSize: 10 }),
    );

    const projection = result.current.columnProjections.get('Todo');
    expect(projection).toBeDefined();
    expect(projection!.renderedRange).toEqual({ start: 0, end: 10 });
    expect(projection!.totalItems).toBe(50);
    expect(projection!.hasMore).toBe(true);
  });

  // ── Totals ──

  it('computes total rendered and dataset items', () => {
    const boardData = createBoardData([
      createBoardColumn('Todo', 25),
      createBoardColumn('In Progress', 15),
      createBoardColumn('Done', 8),
    ]);

    const { result } = renderHook(() =>
      useBoardProjection(boardData, { bufferSize: 10 }),
    );

    // Todo: 10, In Progress: 10, Done: 8 = 28
    expect(result.current.totalRenderedItems).toBe(28);
    expect(result.current.totalDatasetItems).toBe(48);
  });

  // ── Initial Render Complete ──

  it('signals initial render complete after board data is provided', async () => {
    const boardData = createBoardData([createBoardColumn('Todo', 5)]);

    const { result } = renderHook(() => useBoardProjection(boardData));

    await waitFor(() => {
      expect(result.current.isInitialRenderComplete).toBe(true);
    });
  });

  it('resets isInitialRenderComplete when board data becomes null', async () => {
    const boardData = createBoardData([createBoardColumn('Todo', 5)]);

    const { result, rerender } = renderHook(
      ({ data }: { data: BoardDataResponse | null }) => useBoardProjection(data),
      { initialProps: { data: boardData } },
    );

    await waitFor(() => {
      expect(result.current.isInitialRenderComplete).toBe(true);
    });

    rerender({ data: null });

    await waitFor(() => {
      expect(result.current.isInitialRenderComplete).toBe(false);
    });
  });

  // ── Board Data Change Resets Expansions ──

  it('resets expansions when board data reference changes', () => {
    const boardData1 = createBoardData([createBoardColumn('Todo', 50)]);
    const boardData2 = createBoardData([createBoardColumn('Todo', 30)]);

    const { result, rerender } = renderHook(
      ({ data }: { data: BoardDataResponse | null }) =>
        useBoardProjection(data, { bufferSize: 10 }),
      { initialProps: { data: boardData1 } },
    );

    // Initial: rendered 10 of 50
    expect(result.current.columnProjections.get('Todo')!.renderedRange.end).toBe(10);

    // Change board data
    rerender({ data: boardData2 });

    // After reset: rendered 10 of 30
    expect(result.current.columnProjections.get('Todo')!.renderedRange.end).toBe(10);
    expect(result.current.columnProjections.get('Todo')!.totalItems).toBe(30);
  });

  // ── observerRef Factory ──

  it('creates ref callbacks per column id', () => {
    const boardData = createBoardData([createBoardColumn('Todo', 5)]);

    const { result } = renderHook(() => useBoardProjection(boardData));

    const refCallback = result.current.observerRef('Todo');
    expect(typeof refCallback).toBe('function');
  });

  it('cleans up IntersectionObserver when node is set to null', () => {
    const boardData = createBoardData([createBoardColumn('Todo', 5)]);

    const { result } = renderHook(() => useBoardProjection(boardData));

    const refCallback = result.current.observerRef('Todo');

    // Attach
    const mockElement = document.createElement('div');
    refCallback(mockElement);

    // Detach (should not throw)
    refCallback(null);
  });

  // ── Default Config ──

  it('uses default buffer size of 10', () => {
    const boardData = createBoardData([createBoardColumn('Todo', 20)]);

    const { result } = renderHook(() => useBoardProjection(boardData));

    const projection = result.current.columnProjections.get('Todo');
    expect(projection!.renderedRange.end).toBe(10); // default buffer
  });

  // ── Empty Columns ──

  it('handles columns with zero items', () => {
    const boardData = createBoardData([
      createBoardColumn('Empty', 0),
      createBoardColumn('Full', 5),
    ]);

    const { result } = renderHook(() =>
      useBoardProjection(boardData, { bufferSize: 10 }),
    );

    const emptyProjection = result.current.columnProjections.get('Empty');
    expect(emptyProjection).toBeDefined();
    expect(emptyProjection!.renderedRange).toEqual({ start: 0, end: 0 });
    expect(emptyProjection!.totalItems).toBe(0);
    expect(emptyProjection!.hasMore).toBe(false);

    const fullProjection = result.current.columnProjections.get('Full');
    expect(fullProjection!.renderedRange).toEqual({ start: 0, end: 5 });
  });

  // ── Multiple Columns ──

  it('tracks projections independently per column', () => {
    const boardData = createBoardData([
      createBoardColumn('Todo', 30),
      createBoardColumn('In Progress', 5),
      createBoardColumn('Done', 100),
    ]);

    const { result } = renderHook(() =>
      useBoardProjection(boardData, { bufferSize: 10 }),
    );

    expect(result.current.columnProjections.get('Todo')!.hasMore).toBe(true);
    expect(result.current.columnProjections.get('In Progress')!.hasMore).toBe(false);
    expect(result.current.columnProjections.get('Done')!.hasMore).toBe(true);

    expect(result.current.columnProjections.get('Todo')!.renderedRange.end).toBe(10);
    expect(result.current.columnProjections.get('In Progress')!.renderedRange.end).toBe(5);
    expect(result.current.columnProjections.get('Done')!.renderedRange.end).toBe(10);
  });

  // ── Cleanup on unmount ──

  it('does not throw on unmount', () => {
    const boardData = createBoardData([createBoardColumn('Todo', 5)]);

    const { unmount } = renderHook(() => useBoardProjection(boardData));

    expect(() => unmount()).not.toThrow();
  });

  it('disconnects observers on unmount', () => {
    const boardData = createBoardData([createBoardColumn('Todo', 5)]);

    const { result, unmount } = renderHook(() => useBoardProjection(boardData));

    // Attach an observer
    const refCallback = result.current.observerRef('Todo');
    const mockElement = document.createElement('div');
    refCallback(mockElement);

    // Should not throw
    unmount();
  });

  // ── bufferSize exactly matches item count ──

  it('shows hasMore=false when buffer equals item count', () => {
    const boardData = createBoardData([createBoardColumn('Todo', 10)]);

    const { result } = renderHook(() =>
      useBoardProjection(boardData, { bufferSize: 10 }),
    );

    const projection = result.current.columnProjections.get('Todo');
    expect(projection!.renderedRange.end).toBe(10);
    expect(projection!.hasMore).toBe(false);
  });

  // ── Config with custom threshold ──

  it('accepts custom intersection threshold', () => {
    const boardData = createBoardData([createBoardColumn('Todo', 5)]);

    const { result } = renderHook(() =>
      useBoardProjection(boardData, { intersectionThreshold: 0.5 }),
    );

    // Hook should not error with custom threshold
    expect(result.current.columnProjections.size).toBe(1);
  });
});
