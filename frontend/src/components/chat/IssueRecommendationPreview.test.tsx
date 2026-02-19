/**
 * Unit tests for IssueRecommendationPreview component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { IssueRecommendationPreview } from './IssueRecommendationPreview';
import type { IssueCreateActionData, WorkflowResult } from '@/types';

vi.mock('./ChatInterface.css', () => ({}));

function createRecommendation(overrides: Partial<IssueCreateActionData> = {}): IssueCreateActionData {
  return {
    recommendation_id: 'rec-1',
    proposed_title: 'Add dark mode',
    user_story: 'As a user, I want dark mode so I can use the app at night',
    ui_ux_description: 'A toggle switch in the header that switches between light and dark themes',
    functional_requirements: ['Toggle switch in header', 'Persist preference', 'System default detection'],
    metadata: {
      priority: 'P1',
      size: 'M',
      estimate_hours: 8,
      start_date: '2024-02-01',
      target_date: '2024-02-15',
      labels: ['feature', 'frontend'],
    },
    status: 'pending',
    ...overrides,
  };
}

describe('IssueRecommendationPreview', () => {
  it('renders recommendation title, user story, and requirements', () => {
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={vi.fn().mockResolvedValue({ success: true, message: 'ok' })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByText('Add dark mode')).toBeDefined();
    expect(screen.getByText('As a user, I want dark mode so I can use the app at night')).toBeDefined();
    expect(screen.getByText('Toggle switch in header')).toBeDefined();
    expect(screen.getByText('Persist preference')).toBeDefined();
  });

  it('shows metadata section', () => {
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={vi.fn().mockResolvedValue({ success: true, message: 'ok' })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByText('P1')).toBeDefined();
    expect(screen.getByText('M')).toBeDefined();
    expect(screen.getByText('8h')).toBeDefined();
  });

  it('confirm button calls onConfirm', async () => {
    const result: WorkflowResult = { success: true, message: 'Created', issue_number: 42, issue_url: 'https://github.com/issue/42', current_status: 'Todo' };
    const onConfirm = vi.fn().mockResolvedValue(result);
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={onConfirm}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    fireEvent.click(screen.getByText('✓ Confirm & Create Issue'));
    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledWith('rec-1');
    });
  });

  it('shows success result after confirmation', async () => {
    const result: WorkflowResult = { success: true, message: 'Created', issue_number: 42, issue_url: 'https://github.com/issue/42', current_status: 'Todo' };
    const onConfirm = vi.fn().mockResolvedValue(result);
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={onConfirm}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    fireEvent.click(screen.getByText('✓ Confirm & Create Issue'));
    await waitFor(() => {
      expect(screen.getByText('Issue Created Successfully')).toBeDefined();
    });
    expect(screen.getByText(/Issue #42/)).toBeDefined();
  });

  it('shows rejected state when status is rejected', () => {
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation({ status: 'rejected' })}
        onConfirm={vi.fn().mockResolvedValue({ success: true, message: 'ok' })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByText('Recommendation Rejected')).toBeDefined();
  });

  it('shows error message on confirm failure', async () => {
    const onConfirm = vi.fn().mockRejectedValue(new Error('Network error'));
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation()}
        onConfirm={onConfirm}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    fireEvent.click(screen.getByText('✓ Confirm & Create Issue'));
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeDefined();
    });
  });

  it('truncates long UI/UX description (>300 chars)', () => {
    const longDesc = 'A'.repeat(400);
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation({ ui_ux_description: longDesc })}
        onConfirm={vi.fn().mockResolvedValue({ success: true, message: 'ok' })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    const truncated = screen.getByText(/^A+\.\.\.$/);
    expect(truncated.textContent).toBe('A'.repeat(300) + '...');
  });

  it('shows "and X more" for >5 requirements', () => {
    const requirements = [
      'Req 1', 'Req 2', 'Req 3', 'Req 4', 'Req 5', 'Req 6', 'Req 7', 'Req 8',
    ];
    render(
      <IssueRecommendationPreview
        recommendation={createRecommendation({ functional_requirements: requirements })}
        onConfirm={vi.fn().mockResolvedValue({ success: true, message: 'ok' })}
        onReject={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByText('... and 3 more')).toBeDefined();
  });
});
