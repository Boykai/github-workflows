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
});
