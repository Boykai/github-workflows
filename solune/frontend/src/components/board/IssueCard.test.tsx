/**
 * Integration tests for IssueCard interactive states.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, userEvent } from '@/test/test-utils';
import { IssueCard } from './IssueCard';
import type { BoardItem } from '@/types';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

function createBoardItem(overrides: Partial<BoardItem> = {}): BoardItem {
  return {
    item_id: 'item-1',
    content_type: 'issue',
    title: 'Test Issue',
    number: 42,
    repository: { owner: 'testorg', name: 'testrepo' },
    url: 'https://github.com/testorg/testrepo/issues/42',
    status: 'Todo',
    status_option_id: 'opt-1',
    assignees: [],
    linked_prs: [],
    sub_issues: [],
    labels: [],
    ...overrides,
  };
}

describe('IssueCard', () => {
  it('renders issue title and repository info', () => {
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={vi.fn()} />);

    expect(screen.getByText('Test Issue')).toBeInTheDocument();
    expect(screen.getByText(/testorg\/testrepo/)).toBeInTheDocument();
    expect(screen.getByText('#42')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const onClick = vi.fn();
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={onClick} />);

    await userEvent.setup().click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledWith(item);
  });

  it('calls onClick when Enter key is pressed', () => {
    const onClick = vi.fn();
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={onClick} />);

    const card = screen.getByRole('button');
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(onClick).toHaveBeenCalledWith(item);
  });

  it('calls onClick when Space key is pressed', () => {
    const onClick = vi.fn();
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={onClick} />);

    const card = screen.getByRole('button');
    fireEvent.keyDown(card, { key: ' ' });
    expect(onClick).toHaveBeenCalledWith(item);
  });

  it('has tabIndex for keyboard accessibility', () => {
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={vi.fn()} />);
    expect(screen.getByRole('button')).toHaveAttribute('tabindex', '0');
  });

  it('renders assignee avatars', () => {
    const item = createBoardItem({
      assignees: [
        { login: 'user1', avatar_url: 'https://avatar.example.com/1' },
        { login: 'user2', avatar_url: 'https://avatar.example.com/2' },
      ],
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);

    expect(screen.getByAltText('user1')).toBeInTheDocument();
    expect(screen.getByAltText('user2')).toBeInTheDocument();
  });

  it('renders priority and size badges', () => {
    const item = createBoardItem({
      priority: { name: 'P1', color: 'RED' },
      size: { name: 'M', color: 'BLUE' },
      estimate: 5,
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);

    expect(screen.getByText('P1')).toBeInTheDocument();
    expect(screen.getByText('M')).toBeInTheDocument();
    expect(screen.getByText('5pt')).toBeInTheDocument();
  });

  it('shows draft badge for draft issues', () => {
    const item = createBoardItem({
      content_type: 'draft_issue',
      repository: undefined,
      number: undefined,
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);
    expect(screen.getByText('Draft')).toBeInTheDocument();
  });

  it('renders sub-issues count', () => {
    const item = createBoardItem({
      sub_issues: [
        {
          id: 'si-1',
          number: 1,
          title: 'Sub 1',
          url: '#',
          state: 'open',
          assignees: [],
          linked_prs: [],
        },
        {
          id: 'si-2',
          number: 2,
          title: 'Sub 2',
          url: '#',
          state: 'closed',
          assignees: [],
          linked_prs: [],
        },
      ],
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);
    expect(screen.getByText('2 sub-issues')).toBeInTheDocument();
  });

  it('falls back to a safe label color when the API returns invalid label data', () => {
    const item = createBoardItem({
      labels: [{ id: 'lbl-1', name: 'Needs Review', color: 'bad' }],
    });

    render(<IssueCard item={item} onClick={vi.fn()} />);

    expect(screen.getByText('Needs Review')).toHaveStyle({
      color: '#d1d5db',
    });
  });

  it('sets aria-expanded on the sub-issues toggle button', async () => {
    const item = createBoardItem({
      sub_issues: [
        {
          id: 'si-1',
          number: 1,
          title: 'Sub 1',
          url: '#',
          state: 'open',
          assignees: [],
          linked_prs: [],
        },
      ],
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);

    // The card itself has role="button", so filter for the inner toggle button by type attr
    const buttons = screen.getAllByRole('button');
    const toggle = buttons.find((btn) => btn.getAttribute('type') === 'button')!;
    expect(toggle).toBeDefined();
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    await userEvent.setup().click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });

  describe('avatar URL validation (T050/T052)', () => {
    const PLACEHOLDER_SVG_PREFIX = 'data:image/svg+xml,';

    it('renders valid GitHub avatar URLs as-is', () => {
      const item = createBoardItem({
        assignees: [
          {
            login: 'ghuser',
            avatar_url: 'https://avatars.githubusercontent.com/u/12345?v=4',
          },
        ],
      });
      render(<IssueCard item={item} onClick={vi.fn()} />);

      const img = screen.getByAltText('ghuser') as HTMLImageElement;
      expect(img.src).toBe(
        'https://avatars.githubusercontent.com/u/12345?v=4',
      );
    });

    it('replaces non-https avatar URLs with placeholder', () => {
      const item = createBoardItem({
        assignees: [
          { login: 'httpuser', avatar_url: 'http://avatars.githubusercontent.com/u/1' },
        ],
      });
      render(<IssueCard item={item} onClick={vi.fn()} />);

      const img = screen.getByAltText('httpuser') as HTMLImageElement;
      expect(img.src).toContain(PLACEHOLDER_SVG_PREFIX);
    });

    it('replaces non-GitHub domain avatar URLs with placeholder', () => {
      const item = createBoardItem({
        assignees: [
          { login: 'external', avatar_url: 'https://evil.example.com/avatar.png' },
        ],
      });
      render(<IssueCard item={item} onClick={vi.fn()} />);

      const img = screen.getByAltText('external') as HTMLImageElement;
      expect(img.src).toContain(PLACEHOLDER_SVG_PREFIX);
    });

    it('renders placeholder for malformed avatar URLs', () => {
      const item = createBoardItem({
        assignees: [{ login: 'badurl', avatar_url: 'not-a-url' }],
      });
      render(<IssueCard item={item} onClick={vi.fn()} />);

      const img = screen.getByAltText('badurl') as HTMLImageElement;
      expect(img.src).toContain(PLACEHOLDER_SVG_PREFIX);
    });

    it('renders placeholder for empty avatar URL', () => {
      const item = createBoardItem({
        assignees: [{ login: 'noavatar', avatar_url: '' }],
      });
      render(<IssueCard item={item} onClick={vi.fn()} />);

      const img = screen.getByAltText('noavatar') as HTMLImageElement;
      expect(img.src).toContain(PLACEHOLDER_SVG_PREFIX);
    });
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<IssueCard item={createBoardItem()} onClick={vi.fn()} />);
    await expectNoA11yViolations(container);
  });
});
