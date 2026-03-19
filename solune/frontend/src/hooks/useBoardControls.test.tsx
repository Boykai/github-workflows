import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useBoardControls } from './useBoardControls';
import type { BoardDataResponse, BoardItem } from '@/types';

function createBoardItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Alpha issue',
    status: 'Todo',
    status_option_id: 'todo',
    assignees: [],
    linked_prs: [],
    sub_issues: [],
    labels: [],
    ...overrides,
  };
}

function createBoardData(): BoardDataResponse {
  return {
    project: {
      project_id: 'PVT_1',
      name: 'Test Project',
      url: 'https://github.com/orgs/test/projects/1',
      owner_login: 'test',
      status_field: {
        field_id: 'status-field',
        options: [{ option_id: 'todo', name: 'Todo', color: 'GRAY' }],
      },
    },
    columns: [
      {
        status: { option_id: 'todo', name: 'Todo', color: 'GRAY' },
        items: [
          createBoardItem({
            item_id: 'item-1',
            title: 'Alpha issue',
            assignees: [
              { login: 'octocat', avatar_url: 'https://avatars.githubusercontent.com/u/1' },
            ],
            labels: [{ id: 'label-1', name: 'bug', color: 'ff0000' }],
            milestone: 'Sprint 1',
            created_at: '2026-03-01T00:00:00Z',
          }),
          createBoardItem({
            item_id: 'item-2',
            title: 'Beta issue',
            assignees: [
              { login: 'hubot', avatar_url: 'https://avatars.githubusercontent.com/u/2' },
            ],
            labels: [{ id: 'label-2', name: 'feature', color: '00ff00' }],
            milestone: 'Sprint 2',
            created_at: '2026-03-02T00:00:00Z',
          }),
        ],
        item_count: 2,
        estimate_total: 0,
      },
    ],
  };
}

describe('useBoardControls', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('deep-merges persisted controls with safe defaults', () => {
    localStorage.setItem(
      'board-controls-PVT_1',
      JSON.stringify({
        filters: { labels: ['bug'] },
        sort: { field: 'title' },
      })
    );

    const { result } = renderHook(() => useBoardControls('PVT_1', createBoardData()));

    expect(result.current.controls.filters).toEqual({
      labels: ['bug'],
      assignees: [],
      milestones: [],
      pipelineConfig: null,
      priority: [],
    });
    expect(result.current.controls.sort).toEqual({ field: 'title', direction: 'asc' });
    expect(result.current.controls.group).toEqual({ field: null });
  });

  it('filters, sorts, and groups parent issues from the current board data', () => {
    const { result } = renderHook(() => useBoardControls('PVT_1', createBoardData()));

    act(() => {
      result.current.setFilters({ labels: ['feature'], assignees: [], milestones: [] });
      result.current.setSort({ field: 'title', direction: 'desc' });
      result.current.setGroup({ field: 'assignee' });
    });

    const transformedColumn = result.current.transformedData?.columns[0];
    expect(transformedColumn?.items).toHaveLength(1);
    expect(transformedColumn?.items[0].title).toBe('Beta issue');

    const groups = result.current.getGroups(transformedColumn?.items ?? []);
    expect(groups).toEqual([{ name: 'hubot', items: transformedColumn?.items ?? [] }]);
  });

  it('excludes sub-issue cards from the transformed board data', () => {
    const boardData = createBoardData();
    boardData.columns[0].items = [
      createBoardItem({
        item_id: 'parent-1',
        number: 101,
        title: 'Parent issue',
        sub_issues: [
          {
            id: 'sub-1',
            number: 202,
            title: 'Agent sub-issue',
            url: 'https://github.com/test/repo/issues/202',
            state: 'open',
            assignees: [],
            linked_prs: [],
          },
        ],
      }),
      createBoardItem({
        item_id: 'sub-item-1',
        number: 202,
        title: 'Agent sub-issue',
      }),
    ];
    boardData.columns[0].item_count = 2;

    const { result } = renderHook(() => useBoardControls('PVT_1', boardData));

    expect(result.current.transformedData?.columns[0].items.map((item) => item.number)).toEqual([
      101,
    ]);
    expect(result.current.transformedData?.columns[0].item_count).toBe(1);
  });

  it('shows only parent GitHub issues on the board', () => {
    const boardData = createBoardData();
    boardData.columns[0].items = [
      createBoardItem({
        item_id: 'issue-1',
        number: 101,
        title: 'Parent issue',
        content_type: 'issue',
      }),
      createBoardItem({
        item_id: 'draft-1',
        number: 102,
        title: 'Draft issue',
        content_type: 'draft_issue',
      }),
      createBoardItem({
        item_id: 'pr-1',
        number: 103,
        title: 'Linked PR item',
        content_type: 'pull_request',
      }),
    ];
    boardData.columns[0].item_count = 3;

    const { result } = renderHook(() => useBoardControls('PVT_1', boardData));

    expect(result.current.transformedData?.columns[0].items.map((item) => item.title)).toEqual([
      'Parent issue',
    ]);
    expect(result.current.transformedData?.columns[0].item_count).toBe(1);
  });

  it('excludes items with sub-issue label even when not in any parent sub_issues list', () => {
    const boardData = createBoardData();
    boardData.columns[0].items = [
      createBoardItem({
        item_id: 'parent-1',
        number: 101,
        title: 'Parent issue',
      }),
      createBoardItem({
        item_id: 'orphan-sub',
        number: 4137,
        title: '[speckit.specify] Some task',
        labels: [
          { id: 'l1', name: 'ai-generated', color: 'ededed' },
          { id: 'l2', name: 'sub-issue', color: 'ededed' },
        ],
      }),
    ];
    boardData.columns[0].item_count = 2;

    const { result } = renderHook(() => useBoardControls('PVT_1', boardData));

    expect(result.current.transformedData?.columns[0].items.map((item) => item.number)).toEqual([
      101,
    ]);
    expect(result.current.transformedData?.columns[0].item_count).toBe(1);
  });

  it('loads per-project controls before persisting on project switch', async () => {
    localStorage.setItem(
      'board-controls-PVT_1',
      JSON.stringify({ filters: { labels: ['bug'], assignees: [], milestones: [] } })
    );
    localStorage.setItem(
      'board-controls-PVT_2',
      JSON.stringify({ filters: { labels: ['feature'], assignees: [], milestones: [] } })
    );

    const { result, rerender } = renderHook(
      ({ projectId }) => useBoardControls(projectId, createBoardData()),
      { initialProps: { projectId: 'PVT_1' } }
    );

    expect(result.current.controls.filters.labels).toEqual(['bug']);

    rerender({ projectId: 'PVT_2' });

    await waitFor(() => {
      expect(result.current.controls.filters.labels).toEqual(['feature']);
    });

    expect(JSON.parse(localStorage.getItem('board-controls-PVT_2') ?? '{}')).toMatchObject({
      filters: { labels: ['feature'] },
    });
  });
});
