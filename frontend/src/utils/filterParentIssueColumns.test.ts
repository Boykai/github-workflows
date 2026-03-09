import { describe, expect, it } from 'vitest';

import type { BoardColumn, BoardDataResponse, BoardItem } from '@/types';
import { filterParentIssueColumns } from './filterParentIssueColumns';

// ─── Helpers ────────────────────────────────────────────────────────────────

function createItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Test issue',
    number: 1,
    status: 'Todo',
    status_option_id: 'todo',
    assignees: [],
    linked_prs: [],
    sub_issues: [],
    labels: [],
    ...overrides,
  };
}

function createColumn(overrides: Partial<BoardColumn> = {}): BoardColumn {
  return {
    status: { option_id: 'todo', name: 'Todo', color: 'GRAY' },
    items: [],
    item_count: 0,
    estimate_total: 0,
    ...overrides,
  };
}

function createBoardData(columns: BoardColumn[]): BoardDataResponse {
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
    columns,
    rate_limit: null,
  };
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe('filterParentIssueColumns', () => {
  it('returns all issues when none are sub-issues', () => {
    const boardData = createBoardData([
      createColumn({
        items: [
          createItem({ item_id: 'a', number: 1, title: 'Issue A' }),
          createItem({ item_id: 'b', number: 2, title: 'Issue B' }),
        ],
        item_count: 2,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);

    expect(result[0].items).toHaveLength(2);
    expect(result[0].item_count).toBe(2);
  });

  it('excludes items that appear in another item sub_issues array', () => {
    const boardData = createBoardData([
      createColumn({
        items: [
          createItem({
            item_id: 'parent',
            number: 100,
            title: 'Parent',
            sub_issues: [
              {
                id: 'sub-1',
                number: 200,
                title: 'Child',
                url: 'https://github.com/test/repo/issues/200',
                state: 'open',
                assignees: [],
                linked_prs: [],
              },
            ],
          }),
          createItem({ item_id: 'child', number: 200, title: 'Child' }),
        ],
        item_count: 2,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);

    expect(result[0].items).toHaveLength(1);
    expect(result[0].items[0].title).toBe('Parent');
    expect(result[0].item_count).toBe(1);
  });

  it('excludes draft_issue and pull_request content types', () => {
    const boardData = createBoardData([
      createColumn({
        items: [
          createItem({ item_id: 'issue', number: 1, content_type: 'issue', title: 'Issue' }),
          createItem({ item_id: 'draft', number: 2, content_type: 'draft_issue', title: 'Draft' }),
          createItem({ item_id: 'pr', number: 3, content_type: 'pull_request', title: 'PR' }),
        ],
        item_count: 3,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);

    expect(result[0].items).toHaveLength(1);
    expect(result[0].items[0].title).toBe('Issue');
  });

  it('excludes sub-issues while keeping their parent, leaving one item in the column', () => {
    const boardData = createBoardData([
      createColumn({
        items: [
          createItem({
            item_id: 'parent-offboard',
            number: 1,
            sub_issues: [
              {
                id: 's1',
                number: 10,
                title: 'Sub 1',
                url: '',
                state: 'open',
                assignees: [],
                linked_prs: [],
              },
              {
                id: 's2',
                number: 20,
                title: 'Sub 2',
                url: '',
                state: 'open',
                assignees: [],
                linked_prs: [],
              },
            ],
          }),
          createItem({ item_id: 'sub-a', number: 10, title: 'Sub 1' }),
          createItem({ item_id: 'sub-b', number: 20, title: 'Sub 2' }),
        ],
        item_count: 3,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);

    // Only the parent-offboard item remains (it has sub-issues but is itself a parent)
    expect(result[0].items).toHaveLength(1);
    expect(result[0].items[0].item_id).toBe('parent-offboard');
  });

  it('returns empty items when the only items are sub-issues without their parent', () => {
    // Simulate: a parent in column A references sub-issues that live in column B
    const boardData = createBoardData([
      createColumn({
        status: { option_id: 'todo', name: 'Todo', color: 'GRAY' },
        items: [
          createItem({
            item_id: 'parent',
            number: 1,
            sub_issues: [
              {
                id: 's1',
                number: 50,
                title: 'Sub',
                url: '',
                state: 'open',
                assignees: [],
                linked_prs: [],
              },
            ],
          }),
        ],
        item_count: 1,
      }),
      createColumn({
        status: { option_id: 'done', name: 'Done', color: 'GREEN' },
        items: [createItem({ item_id: 'sub', number: 50, title: 'Sub' })],
        item_count: 1,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);

    expect(result[0].items).toHaveLength(1);
    expect(result[0].items[0].title).toBe(boardData.columns[0].items[0].title);
    // Sub-issue in the Done column is excluded
    expect(result[1].items).toHaveLength(0);
    expect(result[1].item_count).toBe(0);
  });

  it('recalculates estimate_total after filtering', () => {
    const boardData = createBoardData([
      createColumn({
        items: [
          createItem({
            item_id: 'parent',
            number: 1,
            estimate: 5,
            sub_issues: [
              {
                id: 's1',
                number: 2,
                title: 'Sub',
                url: '',
                state: 'open',
                assignees: [],
                linked_prs: [],
              },
            ],
          }),
          createItem({ item_id: 'child', number: 2, estimate: 3 }),
        ],
        item_count: 2,
        estimate_total: 8,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);

    expect(result[0].estimate_total).toBe(5);
  });

  it('handles an empty board with no columns gracefully', () => {
    const boardData = createBoardData([]);
    const result = filterParentIssueColumns(boardData);
    expect(result).toEqual([]);
  });

  it('handles columns with no items', () => {
    const boardData = createBoardData([createColumn()]);
    const result = filterParentIssueColumns(boardData);
    expect(result[0].items).toHaveLength(0);
    expect(result[0].item_count).toBe(0);
  });

  it('preserves parent issue metadata (labels, assignees, status)', () => {
    const parent = createItem({
      item_id: 'parent',
      number: 1,
      title: 'Parent Issue',
      assignees: [{ login: 'dev', avatar_url: 'https://example.test/avatar' }],
      labels: [{ id: 'lbl-1', name: 'enhancement', color: '00ff00' }],
      milestone: 'v1.0',
      sub_issues: [
        {
          id: 's1',
          number: 2,
          title: 'Sub',
          url: '',
          state: 'open',
          assignees: [],
          linked_prs: [],
        },
      ],
    });

    const boardData = createBoardData([
      createColumn({
        items: [parent, createItem({ item_id: 'child', number: 2 })],
        item_count: 2,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);
    const parentResult = result[0].items[0];

    expect(parentResult.title).toBe('Parent Issue');
    expect(parentResult.assignees).toHaveLength(1);
    expect(parentResult.labels[0].name).toBe('enhancement');
    expect(parentResult.milestone).toBe('v1.0');
    expect(parentResult.sub_issues).toHaveLength(1);
  });

  it('keeps items with null number (draft issues are excluded by content_type, but issue with null number is kept)', () => {
    const boardData = createBoardData([
      createColumn({
        items: [
          createItem({ item_id: 'no-number', number: undefined, content_type: 'issue' }),
        ],
        item_count: 1,
      }),
    ]);

    const result = filterParentIssueColumns(boardData);

    expect(result[0].items).toHaveLength(1);
  });
});
