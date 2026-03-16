/**
 * Integration tests for TaskPreview — task proposal display and confirmation.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { TaskPreview } from './TaskPreview';
import type { AITaskProposal } from '@/types';

function createProposal(overrides: Partial<AITaskProposal> = {}): AITaskProposal {
  return {
    proposal_id: 'prop-1',
    session_id: 'session-1',
    original_input: 'Create a login page',
    proposed_title: 'Add Login Page',
    proposed_description: 'Implement a login page with email and password fields.',
    status: 'pending',
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 60000).toISOString(),
    ...overrides,
  };
}

describe('TaskPreview', () => {
  it('renders proposal title and description', () => {
    render(<TaskPreview proposal={createProposal()} onConfirm={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByRole('heading', { name: 'Add Login Page' })).toBeInTheDocument();
    expect(screen.getByText(/Implement a login page/)).toBeInTheDocument();
  });

  it('renders Task Preview header', () => {
    render(<TaskPreview proposal={createProposal()} onConfirm={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Task Preview')).toBeInTheDocument();
  });

  it('calls onConfirm when Create Task button is clicked', async () => {
    const onConfirm = vi.fn();
    render(<TaskPreview proposal={createProposal()} onConfirm={onConfirm} onReject={vi.fn()} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Create Task' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onReject when Cancel button is clicked', async () => {
    const onReject = vi.fn();
    render(<TaskPreview proposal={createProposal()} onConfirm={vi.fn()} onReject={onReject} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onReject).toHaveBeenCalledTimes(1);
  });

  it('truncates long descriptions at 500 characters', () => {
    const longDescription = 'A'.repeat(600);
    render(
      <TaskPreview
        proposal={createProposal({ proposed_description: longDescription })}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );
    expect(screen.getByText(/\.\.\.$/)).toBeInTheDocument();
  });

  it('does not render a pipeline badge before confirmation', () => {
    render(
      <TaskPreview
        proposal={createProposal({ pipeline_name: 'Full Review Pipeline' })}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.queryByText(/Agent Pipeline:/)).not.toBeInTheDocument();
  });

  it('renders the pipeline name when the proposal is confirmed', () => {
    render(
      <TaskPreview
        proposal={createProposal({
          status: 'confirmed',
          pipeline_name: 'Full Review Pipeline',
        })}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.getByText('Agent Pipeline: Full Review Pipeline')).toBeInTheDocument();
  });

  it('renders the default pipeline badge when default mappings were used', () => {
    render(
      <TaskPreview
        proposal={createProposal({
          status: 'confirmed',
          pipeline_source: 'default',
        })}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.getByText('Agent Pipeline: Default')).toBeInTheDocument();
  });

  it('renders the custom mappings badge when user mappings were used', () => {
    render(
      <TaskPreview
        proposal={createProposal({
          status: 'confirmed',
          pipeline_source: 'user',
        })}
        onConfirm={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.getByText('Agent Pipeline: Custom Mappings')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <TaskPreview proposal={createProposal()} onConfirm={vi.fn()} onReject={vi.fn()} />
    );
    await expectNoA11yViolations(container);
  });
});
