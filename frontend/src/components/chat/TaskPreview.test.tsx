/**
 * Unit tests for TaskPreview component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskPreview } from './TaskPreview';
import type { AITaskProposal } from '@/types';

function createProposal(overrides: Partial<AITaskProposal> = {}): AITaskProposal {
  return {
    proposal_id: 'prop-1',
    session_id: 'session-1',
    original_input: 'Create a login page',
    proposed_title: 'Implement Login Page',
    proposed_description: 'Build a login page with OAuth support',
    status: 'pending',
    created_at: '2024-01-15T10:00:00Z',
    expires_at: '2024-01-15T11:00:00Z',
    ...overrides,
  };
}

describe('TaskPreview', () => {
  it('renders proposal title and description', () => {
    render(
      <TaskPreview proposal={createProposal()} onConfirm={vi.fn()} onReject={vi.fn()} />
    );
    expect(screen.getByText('Implement Login Page')).toBeDefined();
    expect(screen.getByText('Build a login page with OAuth support')).toBeDefined();
  });

  it('truncates long descriptions (>500 chars)', () => {
    const longDesc = 'A'.repeat(600);
    render(
      <TaskPreview
        proposal={createProposal({ proposed_description: longDesc })}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );
    const truncated = screen.getByText(/^A+\.\.\.$/);
    expect(truncated.textContent).toBe('A'.repeat(500) + '...');
  });

  it('does not truncate descriptions <= 500 chars', () => {
    const desc = 'B'.repeat(500);
    render(
      <TaskPreview
        proposal={createProposal({ proposed_description: desc })}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );
    expect(screen.getByText(desc)).toBeDefined();
  });

  it('calls onConfirm when Create Task button clicked', () => {
    const onConfirm = vi.fn();
    render(
      <TaskPreview proposal={createProposal()} onConfirm={onConfirm} onReject={vi.fn()} />
    );
    fireEvent.click(screen.getByText('Create Task'));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('calls onReject when Cancel button clicked', () => {
    const onReject = vi.fn();
    render(
      <TaskPreview proposal={createProposal()} onConfirm={vi.fn()} onReject={onReject} />
    );
    fireEvent.click(screen.getByText('Cancel'));
    expect(onReject).toHaveBeenCalledOnce();
  });

  it('renders Task Preview label', () => {
    render(
      <TaskPreview proposal={createProposal()} onConfirm={vi.fn()} onReject={vi.fn()} />
    );
    expect(screen.getByText('Task Preview')).toBeDefined();
  });
});
