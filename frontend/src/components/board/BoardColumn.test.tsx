/**
 * Unit tests for BoardColumn component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BoardColumn } from './BoardColumn';
import type { BoardColumn as BoardColumnType, BoardItem } from '@/types';

function createItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Test Issue',
    status: 'Todo',
    status_option_id: 'opt-1',
    assignees: [],
    linked_prs: [],
    ...overrides,
  };
}

function createColumn(overrides: Partial<BoardColumnType> = {}): BoardColumnType {
  return {
    status: {
      option_id: 'opt-1',
      name: 'Todo',
      color: 'BLUE',
    },
    items: [],
    item_count: 0,
    estimate_total: 0,
    ...overrides,
  };
}

describe('BoardColumn', () => {
  it('renders column name and item count', () => {
    render(
      <BoardColumn
        column={createColumn({ item_count: 3 })}
        onCardClick={vi.fn()}
      />
    );
    expect(screen.getByText('Todo')).toBeDefined();
    expect(screen.getByText('3')).toBeDefined();
  });

  it('shows estimate total when > 0', () => {
    render(
      <BoardColumn
        column={createColumn({ estimate_total: 13 })}
        onCardClick={vi.fn()}
      />
    );
    expect(screen.getByText('13pt')).toBeDefined();
  });

  it('does not show estimate total when 0', () => {
    render(
      <BoardColumn
        column={createColumn({ estimate_total: 0 })}
        onCardClick={vi.fn()}
      />
    );
    expect(screen.queryByText(/pt$/)).toBeNull();
  });

  it('shows "No items" when empty', () => {
    render(
      <BoardColumn
        column={createColumn({ items: [] })}
        onCardClick={vi.fn()}
      />
    );
    expect(screen.getByText('No items')).toBeDefined();
  });

  it('renders IssueCard for each item', () => {
    const items = [
      createItem({ item_id: 'item-1', title: 'First Issue' }),
      createItem({ item_id: 'item-2', title: 'Second Issue' }),
    ];
    render(
      <BoardColumn
        column={createColumn({ items, item_count: 2 })}
        onCardClick={vi.fn()}
      />
    );
    expect(screen.getByText('First Issue')).toBeDefined();
    expect(screen.getByText('Second Issue')).toBeDefined();
  });

  it('shows description when present', () => {
    render(
      <BoardColumn
        column={createColumn({
          status: { option_id: 'opt-1', name: 'Todo', color: 'BLUE', description: 'Tasks to do' },
        })}
        onCardClick={vi.fn()}
      />
    );
    expect(screen.getByText('Tasks to do')).toBeDefined();
  });
});
