import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useRecentParentIssues } from './useRecentParentIssues';
import type { BoardDataResponse } from '@/types';

function makeItem(overrides: Record<string, unknown> = {}) {
  return {
    item_id: 'item-1',
    title: 'Test Issue',
    number: 10,
    content_type: 'issue',
    status: 'open',
    labels: [],
    sub_issues: [],
    repository: { owner: 'org', name: 'repo' },
    ...overrides,
  };
}

function makeBoardData(columns: Array<{ name: string; color?: string; items: unknown[] }>): BoardDataResponse {
  return {
    columns: columns.map((col) => ({
      status: { name: col.name, color: col.color ?? 'GREEN' },
      items: col.items,
    })),
  } as BoardDataResponse;
}

describe('useRecentParentIssues', () => {
  it('returns empty array when boardData is null', () => {
    const { result } = renderHook(() => useRecentParentIssues(null));
    expect(result.current).toEqual([]);
  });

  it('returns parent issues from board data', () => {
    const boardData = makeBoardData([
      {
        name: 'Todo',
        color: 'BLUE',
        items: [makeItem({ item_id: 'item-1', title: 'Issue 1', number: 1 })],
      },
    ]);

    const { result } = renderHook(() => useRecentParentIssues(boardData));
    expect(result.current).toHaveLength(1);
    expect(result.current[0].title).toBe('Issue 1');
    expect(result.current[0].status).toBe('Todo');
    expect(result.current[0].statusColor).toBe('BLUE');
  });

  it('excludes non-issue content types', () => {
    const boardData = makeBoardData([
      {
        name: 'Todo',
        items: [
          makeItem({ item_id: 'item-1', content_type: 'draft_issue', number: 1 }),
          makeItem({ item_id: 'item-2', content_type: 'pull_request', number: 2 }),
          makeItem({ item_id: 'item-3', content_type: 'issue', number: 3 }),
        ],
      },
    ]);

    const { result } = renderHook(() => useRecentParentIssues(boardData));
    expect(result.current).toHaveLength(1);
    expect(result.current[0].item_id).toBe('item-3');
  });

  it('excludes sub-issues', () => {
    const parentItem = makeItem({
      item_id: 'parent-1',
      number: 1,
      sub_issues: [{ number: 2 }],
    });
    const subItem = makeItem({ item_id: 'sub-1', number: 2 });

    const boardData = makeBoardData([
      { name: 'Todo', items: [parentItem, subItem] },
    ]);

    const { result } = renderHook(() => useRecentParentIssues(boardData));
    expect(result.current).toHaveLength(1);
    expect(result.current[0].item_id).toBe('parent-1');
  });

  it('excludes items with sub-issue label', () => {
    const boardData = makeBoardData([
      {
        name: 'Todo',
        items: [
          makeItem({
            item_id: 'item-1',
            number: 1,
            labels: [{ name: 'sub-issue' }],
          }),
          makeItem({ item_id: 'item-2', number: 2 }),
        ],
      },
    ]);

    const { result } = renderHook(() => useRecentParentIssues(boardData));
    expect(result.current).toHaveLength(1);
    expect(result.current[0].item_id).toBe('item-2');
  });

  it('deduplicates items by item_id', () => {
    const boardData = makeBoardData([
      { name: 'Todo', items: [makeItem({ item_id: 'item-1', number: 1 })] },
      { name: 'Done', items: [makeItem({ item_id: 'item-1', number: 1 })] },
    ]);

    const { result } = renderHook(() => useRecentParentIssues(boardData));
    expect(result.current).toHaveLength(1);
  });

  it('returns at most 8 items', () => {
    const items = Array.from({ length: 12 }, (_, i) =>
      makeItem({ item_id: `item-${i}`, number: i + 1, title: `Issue ${i + 1}` }),
    );

    const boardData = makeBoardData([{ name: 'Todo', items }]);

    const { result } = renderHook(() => useRecentParentIssues(boardData));
    expect(result.current).toHaveLength(8);
  });

  it('defaults statusColor to GRAY when not specified', () => {
    const boardData = makeBoardData([
      {
        name: 'NoColor',
        items: [makeItem({ item_id: 'item-1', number: 1 })],
      },
    ]);
    // Override the color to null to test default
    (boardData.columns[0].status as Record<string, unknown>).color = null;

    const { result } = renderHook(() => useRecentParentIssues(boardData));
    expect(result.current[0].statusColor).toBe('GRAY');
  });
});
