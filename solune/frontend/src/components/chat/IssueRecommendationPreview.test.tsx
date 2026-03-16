/**
 * Integration tests for IssueRecommendationPreview — confirm/reject workflow.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { IssueRecommendationPreview } from './IssueRecommendationPreview';
import type { IssueCreateActionData, WorkflowResult } from '@/types';

function createRecommendation(
  overrides: Partial<IssueCreateActionData> = {}
): IssueCreateActionData {
  return {
    recommendation_id: 'rec-1',
    proposed_title: 'Add Dark Mode',
    user_story: 'As a user, I want dark mode.',
    ui_ux_description: 'Toggle in settings, applies to all views.',
    functional_requirements: ['Dark mode toggle', 'Persist preference', 'System detection'],
    metadata: {
      priority: 'P1',
      size: 'M',
      estimate_hours: 8,
      start_date: '2026-03-01',
      target_date: '2026-03-15',
      labels: ['feature', 'frontend'],
    },
    status: 'pending',
    ...overrides,
  };
}

describe('IssueRecommendationPreview', () => {
  it('renders recommendation details', () => {
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={vi.fn().mockResolvedValue({ success: true })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByText('Add Dark Mode')).toBeInTheDocument();
    expect(screen.getByText('As a user, I want dark mode.')).toBeInTheDocument();
    expect(screen.getByText('Dark mode toggle')).toBeInTheDocument();
    expect(screen.getByText('Persist preference')).toBeInTheDocument();
  });

  it('renders metadata section', () => {
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={vi.fn().mockResolvedValue({ success: true })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByText('P1')).toBeInTheDocument();
    expect(screen.getByText('M')).toBeInTheDocument();
    expect(screen.getByText('8h')).toBeInTheDocument();
    expect(screen.getByText('feature')).toBeInTheDocument();
    expect(screen.getByText('frontend')).toBeInTheDocument();
  });

  it('calls onConfirm and shows success state', async () => {
    const onConfirm = vi.fn().mockResolvedValue({
      success: true,
      issue_number: 42,
      issue_url: 'https://github.com/org/repo/issues/42',
      current_status: 'Todo',
      message: 'Created',
    } as WorkflowResult);

    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={onConfirm}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );

    await userEvent.setup().click(screen.getByRole('button', { name: /Confirm & Create Issue/i }));
    await waitFor(() => {
      expect(screen.getByText('Issue Created Successfully')).toBeInTheDocument();
    });
    expect(screen.getByText(/Issue #42/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /View on GitHub/i })).toHaveAttribute(
      'href',
      'https://github.com/org/repo/issues/42'
    );
  });

  it('calls onReject', async () => {
    const onReject = vi.fn().mockResolvedValue(undefined);
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={vi.fn().mockResolvedValue({ success: true })}
        onReject={onReject}
      />
    );

    await userEvent.setup().click(screen.getByRole('button', { name: /Reject/i }));
    await waitFor(() => {
      expect(onReject).toHaveBeenCalledWith('rec-1');
    });
  });

  it('shows rejected state', () => {
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation({ status: 'rejected' })}
        onConfirm={vi.fn().mockResolvedValue({ success: true })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByText('Recommendation Rejected')).toBeInTheDocument();
  });

  it('disables buttons when not pending', () => {
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation({ status: 'confirmed' })}
        onConfirm={vi.fn().mockResolvedValue({ success: true })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByRole('button', { name: /Confirm & Create Issue/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Reject/i })).toBeDisabled();
  });

  it('shows error on failed confirm', async () => {
    const onConfirm = vi.fn().mockRejectedValue(new Error('Network error'));
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={onConfirm}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );

    await userEvent.setup().click(screen.getByRole('button', { name: /Confirm & Create Issue/i }));
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={vi.fn().mockResolvedValue({ success: true })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    await expectNoA11yViolations(container);
  });
});
