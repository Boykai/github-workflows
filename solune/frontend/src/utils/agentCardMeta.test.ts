import { describe, expect, it, vi, afterEach } from 'vitest';

import type { BoardDataResponse } from '@/types';
import { countPendingAssignedSubIssues, formatAgentCreatedLabel } from './agentCardMeta';

describe('formatAgentCreatedLabel', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns recently added for agents created within three days', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-08T12:00:00Z'));

    expect(formatAgentCreatedLabel('2026-03-06T13:30:00Z')).toBe('Recently added');
  });

  it('returns the localized creation timestamp after three days', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-08T12:00:00Z'));

    const createdAt = '2026-03-04T09:15:00Z';
    const expected = new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(Date.parse(createdAt));

    expect(formatAgentCreatedLabel(createdAt)).toBe(expected);
  });

  it('falls back to recently added when the timestamp is missing', () => {
    expect(formatAgentCreatedLabel(null)).toBe('Recently added');
  });
});

describe('countPendingAssignedSubIssues', () => {
  function createBoardData(): BoardDataResponse {
    return {
      project: {
        project_id: 'PVT_1',
        owner_login: 'octocat',
        title: 'Test Project',
        url: 'https://github.com/users/octocat/projects/1',
      },
      columns: [
        {
          status: { option_id: 'todo', name: 'Todo', color: 'GRAY' },
          item_count: 2,
          estimate_total: 0,
          items: [
            {
              item_id: 'item-1',
              content_type: 'issue',
              title: 'Parent one',
              status: 'Todo',
              status_option_id: 'todo',
              assignees: [],
              linked_prs: [],
              labels: [],
              sub_issues: [
                {
                  id: 'sub-1',
                  number: 101,
                  title: 'Open alpha',
                  url: 'https://example.test/sub-1',
                  state: 'open',
                  assigned_agent: 'alpha',
                  assignees: [],
                  linked_prs: [],
                },
                {
                  id: 'sub-2',
                  number: 102,
                  title: 'Closed alpha',
                  url: 'https://example.test/sub-2',
                  state: 'closed',
                  assigned_agent: 'alpha',
                  assignees: [],
                  linked_prs: [],
                },
              ],
            },
            {
              item_id: 'item-2',
              content_type: 'issue',
              title: 'Parent two',
              status: 'Todo',
              status_option_id: 'todo',
              assignees: [],
              linked_prs: [],
              labels: [],
              sub_issues: [
                {
                  id: 'sub-3',
                  number: 103,
                  title: 'Open alpha uppercase',
                  url: 'https://example.test/sub-3',
                  state: 'open',
                  assigned_agent: 'ALPHA',
                  assignees: [],
                  linked_prs: [],
                },
                {
                  id: 'sub-4',
                  number: 104,
                  title: 'Open beta',
                  url: 'https://example.test/sub-4',
                  state: 'open',
                  assigned_agent: 'beta',
                  assignees: [],
                  linked_prs: [],
                },
                {
                  id: 'sub-5',
                  number: 105,
                  title: 'Unassigned',
                  url: 'https://example.test/sub-5',
                  state: 'open',
                  assigned_agent: null,
                  assignees: [],
                  linked_prs: [],
                },
              ],
            },
          ],
        },
      ],
    } as BoardDataResponse;
  }

  it('counts only open sub-issues and groups assigned agents case-insensitively', () => {
    expect(countPendingAssignedSubIssues(createBoardData())).toEqual({
      alpha: 2,
      beta: 1,
    });
  });
});
