import { describe, expect, it, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '@/test/test-utils';
import { CleanUpConfirmModal } from './CleanUpConfirmModal';
import type { CleanupPreflightResponse } from '@/types';

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

function makeBranch(
  name: string,
  opts: Partial<{ deletion_reason: string; preservation_reason: string }> = {}
) {
  return {
    name,
    eligible_for_deletion: true,
    linked_issue_number: null,
    linked_issue_title: null,
    linking_method: null,
    preservation_reason: opts.preservation_reason ?? null,
    deletion_reason: opts.deletion_reason ?? null,
  };
}

function makePr(
  number: number,
  title: string,
  opts: Partial<{ deletion_reason: string; preservation_reason: string }> = {}
) {
  return {
    number,
    title,
    head_branch: `feature/${number}`,
    referenced_issues: [] as number[],
    eligible_for_deletion: true,
    preservation_reason: opts.preservation_reason ?? null,
    deletion_reason: opts.deletion_reason ?? null,
  };
}

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

  // ── Section Header Toggle Tests ──

  describe('section header toggles', () => {
    it('toggles all branches to delete when header is clicked', () => {
      renderModal({
        data: createPreflightData({
          branches_to_delete: [
            makeBranch('feature/a', { deletion_reason: 'stale' }),
            makeBranch('feature/b', { deletion_reason: 'stale' }),
          ],
        }),
      });

      // Click the "Branches to Delete" header to preserve all
      fireEvent.click(screen.getByRole('button', { name: 'Toggle all branches to delete' }));

      // All items should now show "Mark for deletion" (meaning they are currently preserved)
      const preserveButtons = screen.getAllByLabelText('Mark for deletion');
      expect(preserveButtons).toHaveLength(2);

      // Click again to revert
      fireEvent.click(screen.getByRole('button', { name: 'Toggle all branches to delete' }));

      const deleteButtons = screen.getAllByLabelText('Preserve this item');
      expect(deleteButtons).toHaveLength(2);
    });

    it('toggles all PRs to close when header is clicked', () => {
      renderModal({
        data: createPreflightData({
          prs_to_close: [
            makePr(10, 'PR A', { deletion_reason: 'stale' }),
            makePr(20, 'PR B', { deletion_reason: 'stale' }),
          ],
        }),
      });

      // Click header to preserve all
      fireEvent.click(
        screen.getByRole('button', { name: 'Toggle all pull requests to close' })
      );

      const preserveButtons = screen.getAllByLabelText('Mark for deletion');
      expect(preserveButtons).toHaveLength(2);

      // Click again to revert
      fireEvent.click(
        screen.getByRole('button', { name: 'Toggle all pull requests to close' })
      );

      const deleteButtons = screen.getAllByLabelText('Preserve this item');
      expect(deleteButtons).toHaveLength(2);
    });

    it('toggles all branches to preserve except main when header is clicked', () => {
      renderModal({
        data: createPreflightData({
          branches_to_preserve: [
            makeBranch('main', { preservation_reason: 'Default protected branch' }),
            makeBranch('develop', { preservation_reason: 'Has linked issues' }),
            makeBranch('feature/active', { preservation_reason: 'Has linked issues' }),
          ],
        }),
      });

      // main is disabled so it has aria-disabled
      const mainToggle = screen
        .getAllByLabelText('Mark for deletion')
        .find((btn) => btn.getAttribute('aria-disabled') === 'true');
      expect(mainToggle).toBeDefined();

      // Click header to mark all for deletion (except main)
      fireEvent.click(
        screen.getByRole('button', { name: 'Toggle all branches to preserve' })
      );

      // develop and feature/active should now show "Preserve this item" (willDelete=true)
      const deleteButtons = screen.getAllByLabelText('Preserve this item');
      expect(deleteButtons).toHaveLength(2);

      // main should still be preserved (disabled, not toggled)
      const mainButtons = screen.getAllByLabelText('Mark for deletion');
      expect(mainButtons).toHaveLength(1);
      expect(mainButtons[0]).toHaveAttribute('aria-disabled', 'true');

      // Click header again to revert
      fireEvent.click(
        screen.getByRole('button', { name: 'Toggle all branches to preserve' })
      );

      // All should be back to "Mark for deletion" (preserved state)
      const allPreserved = screen.getAllByLabelText('Mark for deletion');
      expect(allPreserved).toHaveLength(3);
    });
  });

  // ── Main Branch Protection Tests ──

  describe('main branch protection', () => {
    it('disables toggle for main branch in branches to preserve', () => {
      renderModal({
        data: createPreflightData({
          branches_to_preserve: [
            makeBranch('main', { preservation_reason: 'Default protected branch' }),
            makeBranch('develop', { preservation_reason: 'Has linked issues' }),
          ],
        }),
      });

      // Find the main branch toggle — it should be aria-disabled
      const toggleButtons = screen.getAllByLabelText('Mark for deletion');
      const mainToggle = toggleButtons.find(
        (btn) => btn.getAttribute('aria-disabled') === 'true'
      );
      expect(mainToggle).toBeDefined();

      // Clicking should not change state
      fireEvent.click(mainToggle!);

      // Should still show "Mark for deletion" (preserved) — not toggled
      const afterClick = screen.getAllByLabelText('Mark for deletion');
      expect(
        afterClick.find((btn) => btn.getAttribute('aria-disabled') === 'true')
      ).toBeDefined();
    });

    it('shows "Default branch cannot be deleted" for main', () => {
      renderModal({
        data: createPreflightData({
          branches_to_preserve: [
            makeBranch('main', { preservation_reason: 'Default protected branch' }),
          ],
        }),
      });

      expect(screen.getByText('Default branch cannot be deleted')).toBeInTheDocument();
    });

    it('never includes main in confirm payload after header toggle', () => {
      const onConfirm = vi.fn();
      renderModal({
        onConfirm,
        data: createPreflightData({
          branches_to_delete: [makeBranch('feature/stale', { deletion_reason: 'stale' })],
          branches_to_preserve: [
            makeBranch('main', { preservation_reason: 'Default protected branch' }),
            makeBranch('develop', { preservation_reason: 'Has linked issues' }),
          ],
        }),
      });

      // Toggle all branches to preserve → marks develop for deletion, skips main
      fireEvent.click(
        screen.getByRole('button', { name: 'Toggle all branches to preserve' })
      );

      // Confirm
      fireEvent.click(screen.getByRole('button', { name: 'Confirm Cleanup' }));

      expect(onConfirm).toHaveBeenCalledOnce();
      const payload = onConfirm.mock.calls[0][0];
      expect(payload.branches_to_delete).toContain('feature/stale');
      expect(payload.branches_to_delete).toContain('develop');
      expect(payload.branches_to_delete).not.toContain('main');
    });
  });
});
