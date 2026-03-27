import { describe, expect, it, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '@/test/test-utils';
import { CleanUpConfirmModal } from './CleanUpConfirmModal';
import type { CleanupPreflightResponse, BranchInfo, PullRequestInfo } from '@/types';

// ── Mocks ──

vi.mock('react-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-dom')>();
  return {
    ...actual,
    createPortal: (children: React.ReactNode) => children,
  };
});

vi.mock('@/hooks/useScrollLock', () => ({
  useScrollLock: vi.fn(),
}));

// ── Helpers ──

function createPreflightData(
  overrides: Partial<CleanupPreflightResponse> = {}
): CleanupPreflightResponse {
  return {
    branches_to_delete: [],
    branches_to_preserve: [],
    prs_to_close: [],
    prs_to_preserve: [],
    orphaned_issues: [],
    open_issues_on_board: 3,
    has_permission: true,
    permission_error: null,
    ...overrides,
  };
}

function makeBranch(name: string, extra: Partial<BranchInfo> = {}): BranchInfo {
  return {
    name,
    eligible_for_deletion: true,
    linked_issue_number: null,
    linked_issue_title: null,
    linking_method: null,
    preservation_reason: null,
    deletion_reason: 'stale',
    ...extra,
  };
}

function makePr(number: number, title: string, extra: Partial<PullRequestInfo> = {}): PullRequestInfo {
  return {
    number,
    title,
    head_branch: `feature/${number}`,
    referenced_issues: [],
    eligible_for_deletion: true,
    preservation_reason: null,
    deletion_reason: 'Stale PR',
    ...extra,
  };
}

function renderModal(overrides: Partial<React.ComponentProps<typeof CleanUpConfirmModal>> = {}) {
  const defaultProps: React.ComponentProps<typeof CleanUpConfirmModal> = {
    data: createPreflightData(),
    owner: 'test-owner',
    repo: 'test-repo',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    ...overrides,
  };

  return render(<CleanUpConfirmModal {...defaultProps} />);
}

// ── Tests ──

describe('CleanUpConfirmModal', () => {
  it('renders modal content with title and action buttons', () => {
    renderModal();

    expect(screen.getByText('Confirm Repository Cleanup')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm Cleanup' })).toBeInTheDocument();
  });

  it('calls onCancel when backdrop is clicked', () => {
    const onCancel = vi.fn();
    renderModal({ onCancel });

    // Click the backdrop (the outer div with role="none")
    const backdrop = screen.getByRole('none');
    fireEvent.click(backdrop);

    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('calls onCancel when Escape key is pressed', () => {
    const onCancel = vi.fn();
    renderModal({ onCancel });

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('calls onConfirm when Confirm Cleanup is clicked', () => {
    const onConfirm = vi.fn();
    renderModal({
      onConfirm,
      data: createPreflightData({
        branches_to_delete: [
          {
            name: 'feature/old-branch',
            eligible_for_deletion: true,
            linked_issue_number: null,
            linked_issue_title: null,
            linking_method: null,
            preservation_reason: null,
            deletion_reason: 'stale',
          },
        ],
      }),
    });

    fireEvent.click(screen.getByRole('button', { name: 'Confirm Cleanup' }));

    expect(onConfirm).toHaveBeenCalledOnce();
    expect(onConfirm).toHaveBeenCalledWith(
      expect.objectContaining({
        branches_to_delete: ['feature/old-branch'],
      })
    );
  });

  it('renders branch and PR sections from data', () => {
    renderModal({
      data: createPreflightData({
        branches_to_delete: [
          {
            name: 'feature/stale',
            eligible_for_deletion: true,
            linked_issue_number: null,
            linked_issue_title: null,
            linking_method: null,
            preservation_reason: null,
            deletion_reason: 'No linked issues',
          },
        ],
        prs_to_close: [
          {
            number: 42,
            title: 'Old PR',
            head_branch: 'feature/stale',
            referenced_issues: [],
            eligible_for_deletion: true,
            preservation_reason: null,
            deletion_reason: 'Stale PR',
          },
        ],
      }),
    });

    expect(screen.getByText('feature/stale')).toBeInTheDocument();
    expect(screen.getByText('#42')).toBeInTheDocument();
    expect(screen.getByText('Old PR')).toBeInTheDocument();
  });

  it('disables confirm button when no items to delete', () => {
    renderModal({
      data: createPreflightData(),
    });

    expect(screen.getByRole('button', { name: 'Confirm Cleanup' })).toBeDisabled();
  });

  // ── Type Header Toggle Tests ──

  describe('type header toggle (select all)', () => {
    it('renders header checkboxes for branches and PRs sections', () => {
      renderModal({
        data: createPreflightData({
          branches_to_delete: [makeBranch('feature/a'), makeBranch('feature/b')],
          prs_to_close: [makePr(1, 'PR One')],
        }),
      });

      const branchHeader = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });
      expect(branchHeader).toBeInTheDocument();

      const prHeader = screen.getByRole('checkbox', { name: /Toggle all:.*Pull Requests to Close/i });
      expect(prHeader).toBeInTheDocument();
    });

    it('selects all branches when header is clicked (all initially selected)', () => {
      const onConfirm = vi.fn();
      renderModal({
        onConfirm,
        data: createPreflightData({
          branches_to_delete: [makeBranch('feature/a'), makeBranch('feature/b')],
        }),
      });

      // Header starts checked (all eligible are selected by default)
      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });
      expect(header).toHaveAttribute('aria-checked', 'true');

      // Click to deselect all
      fireEvent.click(header);
      expect(header).toHaveAttribute('aria-checked', 'false');

      // Click again to re-select all
      fireEvent.click(header);
      expect(header).toHaveAttribute('aria-checked', 'true');
    });

    it('shows indeterminate state when some branches are toggled off', () => {
      renderModal({
        data: createPreflightData({
          branches_to_delete: [makeBranch('feature/a'), makeBranch('feature/b')],
        }),
      });

      // Toggle off one branch (preserve it)
      const preserveButtons = screen.getAllByLabelText('Preserve this item');
      fireEvent.click(preserveButtons[0]);

      // Header should now be indeterminate
      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });
      expect(header).toHaveAttribute('aria-checked', 'mixed');
    });

    it('resolves indeterminate to fully selected on header click', () => {
      renderModal({
        data: createPreflightData({
          branches_to_delete: [makeBranch('feature/a'), makeBranch('feature/b')],
        }),
      });

      // Toggle off one branch to get indeterminate state
      const preserveButtons = screen.getAllByLabelText('Preserve this item');
      fireEvent.click(preserveButtons[0]);

      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });
      expect(header).toHaveAttribute('aria-checked', 'mixed');

      // Click header: should select all
      fireEvent.click(header);
      expect(header).toHaveAttribute('aria-checked', 'true');
    });

    it('toggles all PRs via header', () => {
      renderModal({
        data: createPreflightData({
          prs_to_close: [makePr(10, 'PR A'), makePr(20, 'PR B')],
        }),
      });

      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Pull Requests to Close/i });

      // Initially all checked
      expect(header).toHaveAttribute('aria-checked', 'true');

      // Click to deselect all
      fireEvent.click(header);
      expect(header).toHaveAttribute('aria-checked', 'false');

      // Confirm button should be disabled since nothing is selected
      expect(screen.getByRole('button', { name: 'Confirm Cleanup' })).toBeDisabled();

      // Re-select all
      fireEvent.click(header);
      expect(header).toHaveAttribute('aria-checked', 'true');
    });

    it('supports keyboard toggle via Space key on header', () => {
      renderModal({
        data: createPreflightData({
          branches_to_delete: [makeBranch('feature/a')],
        }),
      });

      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });

      // Space key should toggle
      fireEvent.keyDown(header, { key: ' ' });
      expect(header).toHaveAttribute('aria-checked', 'false');

      fireEvent.keyDown(header, { key: ' ' });
      expect(header).toHaveAttribute('aria-checked', 'true');
    });

    it('supports keyboard toggle via Enter key on header', () => {
      renderModal({
        data: createPreflightData({
          branches_to_delete: [makeBranch('feature/a')],
        }),
      });

      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });

      fireEvent.keyDown(header, { key: 'Enter' });
      expect(header).toHaveAttribute('aria-checked', 'false');
    });
  });

  // ── 'main' Branch Protection Tests ──

  describe('main branch protection', () => {
    it('renders main branch with a lock icon and protected label', () => {
      renderModal({
        data: createPreflightData({
          branches_to_preserve: [
            makeBranch('main', {
              eligible_for_deletion: false,
              preservation_reason: 'Default protected branch',
            }),
            makeBranch('feature/ok'),
          ],
        }),
      });

      expect(screen.getByText('main')).toBeInTheDocument();
      expect(screen.getByText('protected')).toBeInTheDocument();
      expect(screen.getByLabelText('Protected branch — cannot be deleted')).toBeInTheDocument();
    });

    it('excludes main branch from header toggle in branches to delete', () => {
      const onConfirm = vi.fn();
      renderModal({
        onConfirm,
        data: createPreflightData({
          branches_to_delete: [
            makeBranch('main', { eligible_for_deletion: false }),
            makeBranch('feature/a'),
            makeBranch('feature/b'),
          ],
        }),
      });

      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });

      // Header should be checked (based on eligible items only, main excluded)
      expect(header).toHaveAttribute('aria-checked', 'true');

      // Confirm should never include 'main'
      fireEvent.click(screen.getByRole('button', { name: 'Confirm Cleanup' }));
      expect(onConfirm).toHaveBeenCalledWith(
        expect.objectContaining({
          branches_to_delete: expect.not.arrayContaining(['main']),
        })
      );
    });

    it('excludes main from header toggle in preserve section', () => {
      renderModal({
        data: createPreflightData({
          branches_to_preserve: [
            makeBranch('main', {
              eligible_for_deletion: false,
              preservation_reason: 'Default protected branch',
            }),
            makeBranch('feature/keep'),
          ],
        }),
      });

      const header = screen.getByRole('checkbox', {
        name: /Toggle all:.*Branches to Preserve/i,
      });

      // Click header to mark all eligible for deletion
      fireEvent.click(header);

      // Main should not have a "Preserve this item" / "Mark for deletion" toggle
      // Only feature/keep should be toggled
      expect(header).toHaveAttribute('aria-checked', 'true');
    });

    it('never includes main in onConfirm payload even if somehow in delete list', () => {
      const onConfirm = vi.fn();
      renderModal({
        onConfirm,
        data: createPreflightData({
          branches_to_delete: [
            makeBranch('main'),
            makeBranch('feature/x'),
          ],
        }),
      });

      fireEvent.click(screen.getByRole('button', { name: 'Confirm Cleanup' }));
      expect(onConfirm).toHaveBeenCalledWith(
        expect.objectContaining({
          branches_to_delete: ['feature/x'],
        })
      );
    });

    it('disables header when only protected branches exist in group', () => {
      renderModal({
        data: createPreflightData({
          branches_to_delete: [
            makeBranch('main', { eligible_for_deletion: false }),
          ],
        }),
      });

      const header = screen.getByRole('checkbox', { name: /Toggle all:.*Branches to Delete/i });
      expect(header).toHaveAttribute('aria-disabled', 'true');
    });

    it('shows checked header when all eligible (non-main) are selected', () => {
      renderModal({
        data: createPreflightData({
          branches_to_preserve: [
            makeBranch('main', {
              eligible_for_deletion: false,
              preservation_reason: 'Default protected branch',
            }),
            makeBranch('feature/a'),
          ],
        }),
      });

      const header = screen.getByRole('checkbox', {
        name: /Toggle all:.*Branches to Preserve/i,
      });

      // Initially unchecked (no preserve branches marked for deletion)
      expect(header).toHaveAttribute('aria-checked', 'false');

      // Click to mark all eligible (feature/a) for deletion
      fireEvent.click(header);
      // Now the only eligible branch is selected → checked
      expect(header).toHaveAttribute('aria-checked', 'true');
    });
  });
});
