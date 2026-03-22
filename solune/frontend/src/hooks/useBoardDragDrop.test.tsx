import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

vi.mock('sonner', () => ({
  toast: Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  }),
}));

import { toast } from 'sonner';
import { useBoardDragDrop } from './useBoardDragDrop';
import type { BoardDataResponse, BoardItem } from '@/types';

const mockToast = toast as unknown as {
  success: ReturnType<typeof vi.fn>;
  error: ReturnType<typeof vi.fn>;
};

const mockItem: BoardItem = {
  item_id: 'item-1',
  content_type: 'Issue',
  title: 'Test Issue',
  status: 'Todo',
  status_option_id: 'opt-1',
  assignees: [],
  linked_prs: [],
  sub_issues: [],
  labels: [],
};

const mockItem2: BoardItem = {
  item_id: 'item-2',
  content_type: 'Issue',
  title: 'Another Issue',
  status: 'In Progress',
  status_option_id: 'opt-2',
  assignees: [],
  linked_prs: [],
  sub_issues: [],
  labels: [],
};

const boardData: BoardDataResponse = {
  project: {
    project_id: 'proj-1',
    name: 'Test',
    url: '',
    owner_login: 'test-owner',
    status_field: {
      field_id: 'sf-1',
      options: [
        { option_id: 'col-1', name: 'Todo', color: 'GRAY' },
        { option_id: 'col-2', name: 'In Progress', color: 'BLUE' },
      ],
    },
  },
  columns: [
    {
      status: { option_id: 'col-1', name: 'Todo', color: 'GRAY' },
      items: [mockItem],
      item_count: 1,
      estimate_total: 0,
    },
    {
      status: { option_id: 'col-2', name: 'In Progress', color: 'BLUE' },
      items: [mockItem2],
      item_count: 1,
      estimate_total: 0,
    },
  ],
};

describe('useBoardDragDrop', () => {
  beforeEach(() => vi.clearAllMocks());

  it('sets activeCard on drag start', () => {
    const { result } = renderHook(() => useBoardDragDrop(boardData));

    act(() => {
      result.current.handlers.onDragStart({
        active: { id: 'item-1' },
      } as never);
    });

    expect(result.current.activeCard).toEqual(mockItem);
  });

  it('sets overColumnId on drag over', () => {
    const { result } = renderHook(() => useBoardDragDrop(boardData));

    act(() => {
      result.current.handlers.onDragOver({
        over: { id: 'column-In Progress' },
      } as never);
    });

    expect(result.current.overColumnId).toBe('column-In Progress');
  });

  it('clears overColumnId when over is null', () => {
    const { result } = renderHook(() => useBoardDragDrop(boardData));

    act(() => {
      result.current.handlers.onDragOver({ over: { id: 'col-1' } } as never);
    });
    expect(result.current.overColumnId).toBe('col-1');

    act(() => {
      result.current.handlers.onDragOver({ over: null } as never);
    });
    expect(result.current.overColumnId).toBeNull();
  });

  it('calls onStatusUpdate and toasts success on drag end to a different column', async () => {
    const onStatusUpdate = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useBoardDragDrop(boardData, onStatusUpdate));

    // Start drag from Todo column
    act(() => {
      result.current.handlers.onDragStart({
        active: { id: 'item-1' },
      } as never);
    });

    // End drag on In Progress column
    await act(async () => {
      await result.current.handlers.onDragEnd({
        active: { id: 'item-1' },
        over: { id: 'column-In Progress' },
      } as never);
    });

    expect(onStatusUpdate).toHaveBeenCalledWith('item-1', 'In Progress');
    expect(mockToast.success).toHaveBeenCalledWith('Issue moved');
    expect(result.current.activeCard).toBeNull();
    expect(result.current.overColumnId).toBeNull();
  });

  it('does not call onStatusUpdate when dropping on the same column', async () => {
    const onStatusUpdate = vi.fn();
    const { result } = renderHook(() => useBoardDragDrop(boardData, onStatusUpdate));

    // Start from Todo
    act(() => {
      result.current.handlers.onDragStart({
        active: { id: 'item-1' },
      } as never);
    });

    // Drop on same column (Todo)
    await act(async () => {
      await result.current.handlers.onDragEnd({
        active: { id: 'item-1' },
        over: { id: 'column-Todo' },
      } as never);
    });

    expect(onStatusUpdate).not.toHaveBeenCalled();
  });

  it('resets all state on drag cancel', () => {
    const { result } = renderHook(() => useBoardDragDrop(boardData));

    act(() => {
      result.current.handlers.onDragStart({
        active: { id: 'item-1' },
      } as never);
    });
    expect(result.current.activeCard).not.toBeNull();

    act(() => {
      result.current.handlers.onDragCancel();
    });

    expect(result.current.activeCard).toBeNull();
    expect(result.current.overColumnId).toBeNull();
  });

  it('toasts error when onStatusUpdate throws', async () => {
    const onStatusUpdate = vi.fn().mockRejectedValue(new Error('API error'));
    const { result } = renderHook(() => useBoardDragDrop(boardData, onStatusUpdate));

    act(() => {
      result.current.handlers.onDragStart({
        active: { id: 'item-1' },
      } as never);
    });

    await act(async () => {
      await result.current.handlers.onDragEnd({
        active: { id: 'item-1' },
        over: { id: 'column-In Progress' },
      } as never);
    });

    expect(mockToast.error).toHaveBeenCalledWith('Failed to move issue', {
      duration: Infinity,
    });
  });

  it('is a no-op when over is null on drag end', async () => {
    const onStatusUpdate = vi.fn();
    const { result } = renderHook(() => useBoardDragDrop(boardData, onStatusUpdate));

    await act(async () => {
      await result.current.handlers.onDragEnd({
        active: { id: 'item-1' },
        over: null,
      } as never);
    });

    expect(onStatusUpdate).not.toHaveBeenCalled();
  });
});
