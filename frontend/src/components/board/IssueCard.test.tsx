/**
 * Integration tests for IssueCard interactive states.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, userEvent } from '@/test/test-utils';
import { IssueCard } from './IssueCard';
import type { BoardItem, PipelineStateInfo } from '@/types';

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

function createPipelineState(overrides: Partial<PipelineStateInfo> = {}): PipelineStateInfo {
  return {
    issue_number: 42,
    project_id: 'proj-1',
    status: 'Ready',
    agents: ['speckit.specify', 'speckit.plan', 'speckit.implement'],
    current_agent_index: 1,
    current_agent: 'speckit.plan',
    completed_agents: ['speckit.specify'],
    is_complete: false,
    started_at: '2026-03-11T00:00:00Z',
    error: null,
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

  it('renders priority badge in header', () => {
    const item = createBoardItem({
      priority: { name: 'P1', color: 'RED' },
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);

    expect(screen.getByText('P1')).toBeInTheDocument();
  });

  it('renders size and estimate badges in footer', () => {
    const item = createBoardItem({
      size: { name: 'M', color: 'BLUE' },
      estimate: 5,
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);

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

  it('renders the blocking badge when blocking queue state marks the issue as blocking', () => {
    const item = createBoardItem();

    render(<IssueCard item={item} onClick={vi.fn()} isBlocking />);

    expect(screen.getByText('Blocking')).toBeInTheDocument();
  });

  it('caps visible labels at 3 and shows overflow count', () => {
    const item = createBoardItem({
      labels: [
        { id: '1', name: 'bug', color: 'ff0000' },
        { id: '2', name: 'feature', color: '00ff00' },
        { id: '3', name: 'urgent', color: '0000ff' },
        { id: '4', name: 'docs', color: 'ff00ff' },
        { id: '5', name: 'test', color: '00ffff' },
      ],
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);

    expect(screen.getByText('bug')).toBeInTheDocument();
    expect(screen.getByText('feature')).toBeInTheDocument();
    expect(screen.getByText('urgent')).toBeInTheDocument();
    expect(screen.getByText('+2')).toBeInTheDocument();
    expect(screen.queryByText('docs')).not.toBeInTheDocument();
  });

  it('renders pipeline health bar when pipelineState is provided', () => {
    const item = createBoardItem();
    const ps = createPipelineState();
    const { container } = render(
      <IssueCard item={item} onClick={vi.fn()} pipelineState={ps} />
    );

    // Health bar should have 3 segments (one per agent)
    const healthBar = container.querySelector('.flex.gap-0\\.5.h-1\\.5');
    expect(healthBar).toBeInTheDocument();
    expect(healthBar?.children.length).toBe(3);
  });

  it('renders active agent chip when pipelineState has current_agent', () => {
    const item = createBoardItem();
    const ps = createPipelineState({ current_agent: 'speckit.plan' });
    render(<IssueCard item={item} onClick={vi.fn()} pipelineState={ps} />);

    expect(screen.getByText('plan')).toBeInTheDocument();
  });

  it('renders pipeline name chip when pipelineName is provided', () => {
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={vi.fn()} pipelineName="My Pipeline" />);

    expect(screen.getByText('My Pipeline')).toBeInTheDocument();
  });

  it('renders error alert icon when pipelineState has error', () => {
    const item = createBoardItem();
    const ps = createPipelineState({ error: 'Agent failed' });
    render(<IssueCard item={item} onClick={vi.fn()} pipelineState={ps} />);

    // AlertTriangle icon should be present with error title
    const alert = screen.getByTitle('Agent failed');
    expect(alert).toBeInTheDocument();
  });

  it('renders PR icon linking to first open PR', () => {
    const item = createBoardItem({
      linked_prs: [
        {
          pr_id: 'pr-1',
          number: 10,
          title: 'Fix bug',
          state: 'open',
          url: 'https://github.com/testorg/testrepo/pull/10',
        },
      ],
    });
    render(<IssueCard item={item} onClick={vi.fn()} />);

    const prLink = screen.getByTitle('PR #10: Fix bug');
    expect(prLink).toBeInTheDocument();
    expect(prLink).toHaveAttribute('href', 'https://github.com/testorg/testrepo/pull/10');
  });

  it('shows delete confirmation on trash icon click and calls onDelete on confirm', async () => {
    const onDelete = vi.fn();
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={vi.fn()} onDelete={onDelete} />);

    const user = userEvent.setup();

    // The delete button should be present
    const deleteBtn = screen.getByTitle('Delete issue and all sub-issues');
    expect(deleteBtn).toBeInTheDocument();

    // Click once — should show confirmation bar
    await user.click(deleteBtn);
    expect(screen.getByText(/Close parent/)).toBeInTheDocument();

    // Click confirm
    await user.click(screen.getByText('Confirm'));
    expect(onDelete).toHaveBeenCalledWith(item);
  });

  it('does not show delete button when onDelete is not provided', () => {
    const item = createBoardItem();
    render(<IssueCard item={item} onClick={vi.fn()} />);

    expect(screen.queryByTitle('Delete issue and all sub-issues')).not.toBeInTheDocument();
  });
});
