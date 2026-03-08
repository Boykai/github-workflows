import { describe, expect, it } from 'vitest';

import type { BoardDataResponse, BoardItem } from '@/types';
import { countParentIssues } from './parentIssueCount';

function createItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_id: 'content-1',
    content_type: 'issue',
    title: 'Parent issue',
    number: 101,
    repository: { owner: 'acme', name: 'repo' },
    url: 'https://example.test/issues/101',
    body: '',
    status: 'Todo',
    status_option_id: 'todo',
    assignees: [],
    priority: undefined,
    size: undefined,
    estimate: undefined,
    linked_prs: [],
    sub_issues: [],
    labels: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    milestone: undefined,
    ...overrides,
  };
}

function createBoardData(items: BoardItem[]): BoardDataResponse {
  return {
    project: {
      project_id: 'PVT_1',
      name: 'Project',
      description: null,
      url: 'https://example.test/project',
      owner_login: 'acme',
      status_field: {
        field_id: 'status-field',
        options: [{ option_id: 'todo', name: 'Todo', color: 'GRAY', description: null }],
      },
    },
    columns: [
      {
        status: { option_id: 'todo', name: 'Todo', color: 'GRAY', description: null },
        items,
        item_count: items.length,
        estimate_total: 0,
      },
    ],
    rate_limit: null,
  };
}

describe('countParentIssues', () => {
  it('returns zero for empty board data', () => {
    expect(countParentIssues(null)).toBe(0);
  });

  it('excludes chore-labeled issues and sub-issues while counting unique parent issues', () => {
    const regularParent = createItem({ item_id: 'parent-1', number: 101 });
    const choreIssue = createItem({
      item_id: 'chore-1',
      number: 102,
      labels: [{ id: 'label-1', name: 'Chore', color: 'ededed' }],
    });
    const parentWithSubIssue = createItem({
      item_id: 'parent-2',
      number: 103,
      sub_issues: [{
        id: 'sub-1',
        number: 201,
        title: 'Sub task',
        url: 'https://example.test/issues/201',
        state: 'open',
        assignees: [],
        linked_prs: [],
      }],
    });
    const subIssueAlsoOnBoard = createItem({ item_id: 'sub-item', number: 201 });
    const duplicatedParent = createItem({ item_id: 'parent-1', number: 101 });

    const boardData = createBoardData([
      regularParent,
      choreIssue,
      parentWithSubIssue,
      subIssueAlsoOnBoard,
      duplicatedParent,
    ]);

    expect(countParentIssues(boardData)).toBe(2);
  });
});