/**
 * Integration tests for BoardColumn empty state rendering.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { BoardColumn } from './BoardColumn';
import type { BoardColumn as BoardColumnType, BoardItem } from '@/types';

function createColumn(overrides: Partial<BoardColumnType> = {}): BoardColumnType {
  return {
    status: { option_id: 'opt-1', name: 'Todo', color: 'GRAY' },
    items: [],
    item_count: 0,
    estimate_total: 0,
    ...overrides,
  };
}

function createBoardItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Test Issue',
    status: 'Todo',
    status_option_id: 'opt-1',
    assignees: [],
    linked_prs: [],
    sub_issues: [],
    labels: [],
    ...overrides,
  };
}

describe('BoardColumn', () => {
  it('renders column header with status name and count', () => {
    const column = createColumn({ item_count: 3 });
    render(<BoardColumn column={column} onCardClick={vi.fn()} />);
    expect(screen.getByText('Todo')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders empty state when no items', () => {
    render(<BoardColumn column={createColumn()} onCardClick={vi.fn()} />);
    expect(screen.getByText('No items')).toBeInTheDocument();
  });

  it('renders items when present', () => {
    const column = createColumn({
      items: [
        createBoardItem({ item_id: 'i1', title: 'First Issue' }),
        createBoardItem({ item_id: 'i2', title: 'Second Issue' }),
      ],
      item_count: 2,
    });
    render(<BoardColumn column={column} onCardClick={vi.fn()} />);
    expect(screen.getByText('First Issue')).toBeInTheDocument();
    expect(screen.getByText('Second Issue')).toBeInTheDocument();
  });

  it('shows estimate total when greater than zero', () => {
    const column = createColumn({ estimate_total: 13 });
    render(<BoardColumn column={column} onCardClick={vi.fn()} />);
    expect(screen.getByText('13pt')).toBeInTheDocument();
  });

  it('calls onCardClick when a card is clicked', async () => {
    const onCardClick = vi.fn();
    const item = createBoardItem({ title: 'Clickable Issue' });
    const column = createColumn({ items: [item], item_count: 1 });
    render(<BoardColumn column={column} onCardClick={onCardClick} />);

    await userEvent.setup().click(screen.getByText('Clickable Issue'));
    expect(onCardClick).toHaveBeenCalledWith(item);
  });

  // ── Performance regression: memo boundary (Spec 034 T029) ──

  it('is wrapped in React.memo (prevents unnecessary rerenders)', () => {
    // BoardColumn is exported as a memo component — verify the wrapper exists.
    // React.memo components have a $$typeof of Symbol(react.memo).
    expect(BoardColumn).toHaveProperty('$$typeof');
    const typeofVal = (BoardColumn as unknown as { $$typeof: symbol }).$$typeof;
    expect(typeofVal.toString()).toContain('memo');
  });
});
