import { describe, it, expect } from 'vitest';
import { BoardDataResponseSchema } from './board';

const minimalBoardItem = {
  item_id: 'item-1',
  content_type: 'issue' as const,
  title: 'Fix bug',
  status: 'Todo',
  status_option_id: 'opt-1',
  assignees: [],
  linked_prs: [],
  sub_issues: [],
  labels: [],
};

const fullBoardData = {
  project: {
    project_id: 'PVT_abc',
    name: 'My Project',
    url: 'https://github.com/orgs/test/projects/1',
    owner_login: 'test-org',
    status_field: {
      field_id: 'field-1',
      options: [
        { option_id: 'opt-1', name: 'Todo', color: 'GRAY' as const },
        { option_id: 'opt-2', name: 'Done', color: 'GREEN' as const },
      ],
    },
  },
  columns: [
    {
      status: { option_id: 'opt-1', name: 'Todo', color: 'GRAY' as const },
      items: [minimalBoardItem],
      item_count: 1,
      estimate_total: 0,
    },
  ],
  rate_limit: null,
};

describe('BoardDataResponseSchema', () => {
  it('parses valid full board data', () => {
    const result = BoardDataResponseSchema.parse(fullBoardData);
    expect(result.project.project_id).toBe('PVT_abc');
    expect(result.columns).toHaveLength(1);
  });

  it('parses board with empty columns', () => {
    const data = { ...fullBoardData, columns: [] };
    expect(BoardDataResponseSchema.parse(data).columns).toEqual([]);
  });

  it('parses board item with all optional fields', () => {
    const richItem = {
      ...minimalBoardItem,
      content_id: 'content-1',
      number: 42,
      repository: { owner: 'test-org', name: 'test-repo' },
      url: 'https://github.com/test-org/test-repo/issues/42',
      body: 'Description here',
      priority: { name: 'High', color: 'RED' as const },
      size: { name: 'M' },
      estimate: 5,
      issue_type: 'bug',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      milestone: 'v1.0',
    };
    const data = {
      ...fullBoardData,
      columns: [{ ...fullBoardData.columns[0], items: [richItem] }],
    };
    const result = BoardDataResponseSchema.parse(data);
    expect(result.columns[0].items[0].number).toBe(42);
    expect(result.columns[0].items[0].priority?.name).toBe('High');
  });

  it('parses linked PRs in board items', () => {
    const itemWithPR = {
      ...minimalBoardItem,
      linked_prs: [
        { pr_id: 'pr-1', number: 10, title: 'Fix it', state: 'open' as const, url: 'https://github.com/pr/10' },
      ],
    };
    const data = {
      ...fullBoardData,
      columns: [{ ...fullBoardData.columns[0], items: [itemWithPR] }],
    };
    const result = BoardDataResponseSchema.parse(data);
    expect(result.columns[0].items[0].linked_prs[0].state).toBe('open');
  });

  it('parses sub-issues', () => {
    const itemWithSub = {
      ...minimalBoardItem,
      sub_issues: [
        {
          id: 'sub-1',
          number: 5,
          title: 'Sub task',
          url: 'https://github.com/issues/5',
          state: 'open',
          assigned_agent: null,
          assignees: [{ login: 'user1', avatar_url: 'https://avatar.example.com' }],
          linked_prs: [],
        },
      ],
    };
    const data = {
      ...fullBoardData,
      columns: [{ ...fullBoardData.columns[0], items: [itemWithSub] }],
    };
    const result = BoardDataResponseSchema.parse(data);
    expect(result.columns[0].items[0].sub_issues[0].title).toBe('Sub task');
  });

  it('accepts rate_limit info', () => {
    const data = {
      ...fullBoardData,
      rate_limit: { limit: 5000, remaining: 4999, reset_at: 1700000000, used: 1 },
    };
    const result = BoardDataResponseSchema.parse(data);
    expect(result.rate_limit?.remaining).toBe(4999);
  });

  it('rejects invalid content_type', () => {
    const badItem = { ...minimalBoardItem, content_type: 'unknown' };
    const data = {
      ...fullBoardData,
      columns: [{ ...fullBoardData.columns[0], items: [badItem] }],
    };
    expect(() => BoardDataResponseSchema.parse(data)).toThrow();
  });

  it('rejects missing project', () => {
    const { project: _, ...rest } = fullBoardData;
    expect(() => BoardDataResponseSchema.parse(rest)).toThrow();
  });

  it('accepts all status colors', () => {
    const colors = ['GRAY', 'BLUE', 'GREEN', 'YELLOW', 'ORANGE', 'RED', 'PINK', 'PURPLE'] as const;
    for (const color of colors) {
      const data = {
        ...fullBoardData,
        columns: [
          {
            ...fullBoardData.columns[0],
            status: { option_id: 'opt-1', name: 'Test', color },
          },
        ],
      };
      expect(BoardDataResponseSchema.parse(data).columns[0].status.color).toBe(color);
    }
  });
});
