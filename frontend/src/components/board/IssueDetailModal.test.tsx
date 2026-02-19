/**
 * Unit tests for IssueDetailModal component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { IssueDetailModal } from './IssueDetailModal';
import type { BoardItem } from '@/types';

function createItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Fix authentication bug',
    status: 'In Progress',
    status_option_id: 'opt-1',
    assignees: [],
    linked_prs: [],
    repository: { owner: 'acme', name: 'webapp' },
    number: 42,
    url: 'https://github.com/acme/webapp/issues/42',
    ...overrides,
  };
}

describe('IssueDetailModal', () => {
  it('renders item title, status, and repo info', () => {
    render(<IssueDetailModal item={createItem()} onClose={vi.fn()} />);
    expect(screen.getByText('Fix authentication bug')).toBeDefined();
    expect(screen.getByText('In Progress')).toBeDefined();
    expect(screen.getByText(/acme\/webapp/)).toBeDefined();
  });

  it('shows draft badge for draft issues', () => {
    render(
      <IssueDetailModal item={createItem({ content_type: 'draft_issue' })} onClose={vi.fn()} />
    );
    expect(screen.getByText('Draft')).toBeDefined();
  });

  it('close button calls onClose', () => {
    const onClose = vi.fn();
    render(<IssueDetailModal item={createItem()} onClose={onClose} />);
    fireEvent.click(screen.getByLabelText('Close modal'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('Escape key calls onClose', () => {
    const onClose = vi.fn();
    render(<IssueDetailModal item={createItem()} onClose={onClose} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('backdrop click calls onClose', () => {
    const onClose = vi.fn();
    const { container } = render(<IssueDetailModal item={createItem()} onClose={onClose} />);
    const backdrop = container.querySelector('.modal-backdrop')!;
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('shows priority, size, estimate fields', () => {
    render(
      <IssueDetailModal
        item={createItem({
          priority: { name: 'P0', color: 'RED' },
          size: { name: 'L', color: 'YELLOW' },
          estimate: 5,
        })}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText('P0')).toBeDefined();
    expect(screen.getByText('L')).toBeDefined();
    expect(screen.getByText('5 points')).toBeDefined();
  });

  it('shows assignees', () => {
    render(
      <IssueDetailModal
        item={createItem({
          assignees: [
            { login: 'alice', avatar_url: 'https://avatar.example.com/alice' },
            { login: 'bob', avatar_url: 'https://avatar.example.com/bob' },
          ],
        })}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText('alice')).toBeDefined();
    expect(screen.getByText('bob')).toBeDefined();
  });

  it('shows body/description', () => {
    render(
      <IssueDetailModal
        item={createItem({ body: 'This is the issue description.' })}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText('This is the issue description.')).toBeDefined();
  });

  it('shows linked PRs with correct state labels', () => {
    render(
      <IssueDetailModal
        item={createItem({
          linked_prs: [
            { pr_id: 'pr-1', number: 10, title: 'Fix auth', state: 'open', url: 'https://github.com/pr/10' },
            { pr_id: 'pr-2', number: 11, title: 'Merge fix', state: 'merged', url: 'https://github.com/pr/11' },
            { pr_id: 'pr-3', number: 12, title: 'Closed PR', state: 'closed', url: 'https://github.com/pr/12' },
          ],
        })}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText('Open')).toBeDefined();
    expect(screen.getByText('Merged')).toBeDefined();
    expect(screen.getByText('Closed')).toBeDefined();
  });

  it('shows "Open in GitHub" link', () => {
    render(<IssueDetailModal item={createItem()} onClose={vi.fn()} />);
    expect(screen.getByText('Open in GitHub ↗')).toBeDefined();
  });
});
