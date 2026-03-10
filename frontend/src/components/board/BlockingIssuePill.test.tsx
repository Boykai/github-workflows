/**
 * Tests for BlockingIssuePill component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen, userEvent, createTestQueryClient } from '@/test/test-utils';
import { QueryClientProvider } from '@tanstack/react-query';
import { BlockingIssuePill } from './BlockingIssuePill';
import type { BlockingQueueEntry } from '@/types';

function makeEntry(overrides: Partial<BlockingQueueEntry> = {}): BlockingQueueEntry {
  return {
    id: 1,
    repo_key: 'owner/repo',
    issue_number: 42,
    project_id: 'PVT_test',
    is_blocking: true,
    queue_status: 'active',
    parent_branch: 'issue-42',
    blocking_source_issue: null,
    created_at: '2025-01-01T00:00:00Z',
    activated_at: '2025-01-01T00:01:00Z',
    completed_at: null,
    ...overrides,
  };
}

function renderPill(entries: BlockingQueueEntry[], projectId = 'PVT_test') {
  const qc = createTestQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <BlockingIssuePill entries={entries} projectId={projectId} />
    </QueryClientProvider>
  );
}

describe('BlockingIssuePill', () => {
  it('renders nothing when no active blocking issues exist', () => {
    const entries: BlockingQueueEntry[] = [
      makeEntry({ queue_status: 'pending', is_blocking: false, issue_number: 1 }),
    ];
    const { container } = renderPill(entries);
    // Only the wrapping divs from providers — no pill content
    expect(container.querySelector('[title]')).toBeNull();
  });

  it('renders the oldest active blocking issue number', () => {
    renderPill([makeEntry({ issue_number: 42 })]);
    expect(screen.getByText('#42')).toBeInTheDocument();
  });

  it('links to the correct GitHub issue URL', () => {
    renderPill([makeEntry({ issue_number: 42, repo_key: 'myorg/myrepo' })]);
    const link = screen.getByTitle('Open issue #42 on GitHub');
    expect(link).toHaveAttribute('href', 'https://github.com/myorg/myrepo/issues/42');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('renders skip and delete buttons', () => {
    renderPill([makeEntry()]);
    expect(screen.getByTitle('Skip to next blocking issue')).toBeInTheDocument();
    expect(screen.getByTitle('Close issue on GitHub and skip')).toBeInTheDocument();
  });

  it('shows confirmation dialog when delete is clicked', async () => {
    renderPill([makeEntry({ issue_number: 42 })]);
    const user = userEvent.setup();
    await user.click(screen.getByTitle('Close issue on GitHub and skip'));
    expect(screen.getByText('Close Blocking Issue')).toBeInTheDocument();
    expect(screen.getByText(/close issue #42 on GitHub/i)).toBeInTheDocument();
    expect(screen.getByText('Close & Skip')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('shows in_review entry as the oldest when no active exists', () => {
    const entries = [
      makeEntry({ issue_number: 10, queue_status: 'in_review', is_blocking: true }),
      makeEntry({ id: 2, issue_number: 20, queue_status: 'pending', is_blocking: true }),
    ];
    renderPill(entries);
    expect(screen.getByText('#10')).toBeInTheDocument();
  });

  it('picks the first (oldest) active blocking from multiple entries', () => {
    const entries = [
      makeEntry({
        id: 1,
        issue_number: 5,
        queue_status: 'active',
        is_blocking: true,
        created_at: '2025-01-01T00:00:00Z',
      }),
      makeEntry({
        id: 2,
        issue_number: 15,
        queue_status: 'active',
        is_blocking: true,
        created_at: '2025-01-02T00:00:00Z',
      }),
    ];
    renderPill(entries);
    // First = oldest (sorted by created_at ASC from backend)
    expect(screen.getByText('#5')).toBeInTheDocument();
  });
});
