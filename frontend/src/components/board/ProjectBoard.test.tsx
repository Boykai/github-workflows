/**
 * Unit tests for ProjectBoard component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProjectBoard } from './ProjectBoard';
import type { BoardDataResponse } from '@/types';

function createBoardData(): BoardDataResponse {
  return {
    project: {
      project_id: 'proj-1',
      name: 'Test Project',
      url: 'https://github.com/orgs/test/projects/1',
      owner_login: 'test-org',
      status_field: {
        field_id: 'field-1',
        options: [],
      },
    },
    columns: [
      {
        status: { option_id: 'opt-1', name: 'Todo', color: 'BLUE' },
        items: [],
        item_count: 0,
        estimate_total: 0,
      },
      {
        status: { option_id: 'opt-2', name: 'In Progress', color: 'YELLOW' },
        items: [
          {
            item_id: 'item-1',
            content_type: 'issue',
            title: 'Active Task',
            status: 'In Progress',
            status_option_id: 'opt-2',
            assignees: [],
            linked_prs: [],
          },
        ],
        item_count: 1,
        estimate_total: 5,
      },
      {
        status: { option_id: 'opt-3', name: 'Done', color: 'GREEN' },
        items: [],
        item_count: 0,
        estimate_total: 0,
      },
    ],
  };
}

describe('ProjectBoard', () => {
  it('renders columns from boardData', () => {
    render(<ProjectBoard boardData={createBoardData()} onCardClick={vi.fn()} />);
    expect(screen.getByText('Todo')).toBeDefined();
    expect(screen.getByText('In Progress')).toBeDefined();
    expect(screen.getByText('Done')).toBeDefined();
  });

  it('renders items within columns', () => {
    render(<ProjectBoard boardData={createBoardData()} onCardClick={vi.fn()} />);
    expect(screen.getByText('Active Task')).toBeDefined();
  });
});
