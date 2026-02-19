/**
 * Unit tests for IssueCard component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { IssueCard } from './IssueCard';
import type { BoardItem } from '@/types';

function createItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Fix authentication bug',
    status: 'Todo',
    status_option_id: 'opt-1',
    assignees: [],
    linked_prs: [],
    ...overrides,
  };
}

describe('IssueCard', () => {
  it('renders title', () => {
    render(<IssueCard item={createItem()} onClick={vi.fn()} />);
    expect(screen.getByText('Fix authentication bug')).toBeDefined();
  });

  it('shows repo + issue number', () => {
    render(
      <IssueCard
        item={createItem({
          repository: { owner: 'acme', name: 'webapp' },
          number: 42,
        })}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('acme/webapp')).toBeDefined();
    expect(screen.getByText('#42')).toBeDefined();
  });

  it('shows draft badge for draft issues', () => {
    render(
      <IssueCard
        item={createItem({ content_type: 'draft_issue' })}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('Draft')).toBeDefined();
  });

  it('shows priority badge', () => {
    render(
      <IssueCard
        item={createItem({ priority: { name: 'P0', color: 'RED' } })}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('P0')).toBeDefined();
  });

  it('shows size badge', () => {
    render(
      <IssueCard
        item={createItem({ size: { name: 'M', color: 'YELLOW' } })}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('M')).toBeDefined();
  });

  it('shows estimate badge', () => {
    render(
      <IssueCard
        item={createItem({ estimate: 8 })}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('8pt')).toBeDefined();
  });

  it('shows assignee avatars', () => {
    render(
      <IssueCard
        item={createItem({
          assignees: [
            { login: 'alice', avatar_url: 'https://avatar.example.com/alice' },
            { login: 'bob', avatar_url: 'https://avatar.example.com/bob' },
          ],
        })}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByAltText('alice')).toBeDefined();
    expect(screen.getByAltText('bob')).toBeDefined();
  });

  it('shows linked PR count', () => {
    render(
      <IssueCard
        item={createItem({
          linked_prs: [
            { pr_id: 'pr-1', number: 10, title: 'PR 1', state: 'open', url: 'https://example.com' },
            { pr_id: 'pr-2', number: 11, title: 'PR 2', state: 'merged', url: 'https://example.com' },
          ],
        })}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('2')).toBeDefined();
  });

  it('clicking calls onClick with item', () => {
    const onClick = vi.fn();
    const item = createItem();
    render(<IssueCard item={item} onClick={onClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledWith(item);
  });

  it('keyboard Enter triggers onClick', () => {
    const onClick = vi.fn();
    const item = createItem();
    render(<IssueCard item={item} onClick={onClick} />);
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onClick).toHaveBeenCalledWith(item);
  });

  it('keyboard Space triggers onClick', () => {
    const onClick = vi.fn();
    const item = createItem();
    render(<IssueCard item={item} onClick={onClick} />);
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(onClick).toHaveBeenCalledWith(item);
  });
});
