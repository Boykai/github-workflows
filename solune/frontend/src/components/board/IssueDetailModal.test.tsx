/**
 * Integration tests for IssueDetailModal open/close and keyboard dismiss.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, userEvent } from '@/test/test-utils';
import { IssueDetailModal } from './IssueDetailModal';
import type { BoardItem } from '@/types';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

function createBoardItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Test Issue Title',
    number: 42,
    repository: { owner: 'testorg', name: 'testrepo' },
    url: 'https://github.com/testorg/testrepo/issues/42',
    body: 'This is a test issue description.',
    status: 'Todo',
    status_option_id: 'opt-1',
    assignees: [],
    linked_prs: [],
    sub_issues: [],
    labels: [],
    ...overrides,
  };
}

describe('IssueDetailModal', () => {
  it('renders issue title and details', () => {
    const item = createBoardItem();
    render(<IssueDetailModal item={item} onClose={vi.fn()} />);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Test Issue Title' })).toBeInTheDocument();
    expect(screen.getByText('This is a test issue description.')).toBeInTheDocument();
    expect(screen.getByText('Todo')).toBeInTheDocument();
  });

  it('calls onClose when Escape key is pressed', () => {
    const onClose = vi.fn();
    render(<IssueDetailModal item={createBoardItem()} onClose={onClose} />);

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when close button is clicked', async () => {
    const onClose = vi.fn();
    render(<IssueDetailModal item={createBoardItem()} onClose={onClose} />);

    const closeBtn = screen.getByRole('button', { name: 'Close modal' });
    await userEvent.setup().click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('has proper ARIA attributes for dialog', () => {
    const item = createBoardItem();
    render(<IssueDetailModal item={item} onClose={vi.fn()} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'issue-detail-modal-title');

    const heading = screen.getByRole('heading', { name: 'Test Issue Title' });
    expect(heading).toHaveAttribute('id', 'issue-detail-modal-title');
  });

  it('renders repository info', () => {
    render(<IssueDetailModal item={createBoardItem()} onClose={vi.fn()} />);
    expect(screen.getByText(/testorg\/testrepo/)).toBeInTheDocument();
    expect(screen.getByText(/#42/)).toBeInTheDocument();
  });

  it('renders assignees when present', () => {
    const item = createBoardItem({
      assignees: [{ login: 'user1', avatar_url: 'https://avatar.example.com/1' }],
    });
    render(<IssueDetailModal item={item} onClose={vi.fn()} />);

    expect(screen.getByText('Assignees')).toBeInTheDocument();
    expect(screen.getByText('user1')).toBeInTheDocument();
  });

  it('renders linked PRs when present', () => {
    const item = createBoardItem({
      linked_prs: [
        {
          pr_id: 'pr-1',
          number: 99,
          title: 'Fix bug',
          state: 'open',
          url: 'https://github.com/pr/99',
        },
      ],
    });
    render(<IssueDetailModal item={item} onClose={vi.fn()} />);

    expect(screen.getByText('Linked Pull Requests')).toBeInTheDocument();
    expect(screen.getByText('Fix bug')).toBeInTheDocument();
  });

  it('renders Open in GitHub link', () => {
    render(<IssueDetailModal item={createBoardItem()} onClose={vi.fn()} />);
    const link = screen.getByRole('link', { name: /Open in GitHub/i });
    expect(link).toHaveAttribute('href', 'https://github.com/testorg/testrepo/issues/42');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('traps focus within the dialog on Tab', () => {
    render(<IssueDetailModal item={createBoardItem()} onClose={vi.fn()} />);

    const dialog = screen.getByRole('dialog');
    const focusableElements = dialog.querySelectorAll<HTMLElement>(
      'button:not([disabled]), a[href]'
    );
    expect(focusableElements.length).toBeGreaterThanOrEqual(2);

    const last = focusableElements[focusableElements.length - 1];
    last.focus();

    // Tab from last element should wrap to first
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(focusableElements[0]);
  });

  it('traps focus within the dialog on Shift+Tab', () => {
    render(<IssueDetailModal item={createBoardItem()} onClose={vi.fn()} />);

    const dialog = screen.getByRole('dialog');
    const focusableElements = dialog.querySelectorAll<HTMLElement>(
      'button:not([disabled]), a[href]'
    );
    expect(focusableElements.length).toBeGreaterThanOrEqual(2);

    const first = focusableElements[0];
    first.focus();

    // Shift+Tab from first element should wrap to last
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(focusableElements[focusableElements.length - 1]);
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<IssueDetailModal item={createBoardItem()} onClose={vi.fn()} />);
    await expectNoA11yViolations(container);
  });
});
