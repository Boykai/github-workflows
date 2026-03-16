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
      sub_issues: [
        {
          id: 'sub-1',
          number: 201,
          title: 'Sub task',
          url: 'https://example.test/issues/201',
          state: 'open',
          assignees: [],
          linked_prs: [],
        },
      ],
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

  it('excludes issues with Chore issue type even when they have no chore label', () => {
    const regularParent = createItem({ item_id: 'parent-1', number: 101 });
    const choreByType = createItem({
      item_id: 'chore-type-1',
      number: 102,
      issue_type: 'Chore',
      labels: [],
    });
    const choreByLabel = createItem({
      item_id: 'chore-label-1',
      number: 103,
      labels: [{ id: 'label-1', name: 'chore', color: 'ededed' }],
    });
    const anotherParent = createItem({ item_id: 'parent-2', number: 104 });

    const boardData = createBoardData([regularParent, choreByType, choreByLabel, anotherParent]);

    expect(countParentIssues(boardData)).toBe(2);
  });

  it('handles issue_type check case-insensitively', () => {
    const parent = createItem({ item_id: 'parent-1', number: 101 });
    const choreLowercase = createItem({
      item_id: 'chore-lc',
      number: 102,
      issue_type: 'chore',
    });
    const choreUppercase = createItem({
      item_id: 'chore-uc',
      number: 103,
      issue_type: 'CHORE',
    });

    const boardData = createBoardData([parent, choreLowercase, choreUppercase]);

    expect(countParentIssues(boardData)).toBe(1);
  });

  it('counts issues when issue_type is undefined or null', () => {
    const withoutType = createItem({ item_id: 'p1', number: 101 });
    const withBugType = createItem({ item_id: 'p2', number: 102, issue_type: 'Bug' });
    const withUndefinedType = createItem({ item_id: 'p3', number: 103, issue_type: undefined });
    // Backend sends JSON null for missing issue_type; cast to exercise that runtime path
    const withNullType = createItem({
      item_id: 'p4',
      number: 104,
      issue_type: null as unknown as string | undefined,
    });

    const boardData = createBoardData([withoutType, withBugType, withUndefinedType, withNullType]);

    expect(countParentIssues(boardData)).toBe(4);
  });

  it('returns zero when all issues are chore type', () => {
    const chore1 = createItem({ item_id: 'c1', number: 101, issue_type: 'Chore' });
    const chore2 = createItem({
      item_id: 'c2',
      number: 102,
      labels: [{ id: 'l1', name: 'chore', color: 'ededed' }],
    });

    const boardData = createBoardData([chore1, chore2]);

    expect(countParentIssues(boardData)).toBe(0);
  });

  it('excludes issues with sub-issue label even when not in any parent sub_issues list', () => {
    const parent = createItem({ item_id: 'parent-1', number: 101 });
    const subIssueByLabel = createItem({
      item_id: 'sub-label-1',
      number: 201,
      title: '[speckit.specify] Some task',
      labels: [
        { id: 'l1', name: 'ai-generated', color: 'ededed' },
        { id: 'l2', name: 'sub-issue', color: 'ededed' },
      ],
    });
    const anotherParent = createItem({ item_id: 'parent-2', number: 102 });

    const boardData = createBoardData([parent, subIssueByLabel, anotherParent]);

    // sub-issue label should exclude the item, leaving 2 parents
    expect(countParentIssues(boardData)).toBe(2);
  });
});
