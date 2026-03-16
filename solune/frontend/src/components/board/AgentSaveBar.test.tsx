/**
 * Integration tests for AgentSaveBar — save/discard visibility and actions.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { AgentSaveBar } from './AgentSaveBar';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('AgentSaveBar', () => {
  const defaultProps = {
    onSave: vi.fn(),
    onDiscard: vi.fn(),
    isSaving: false,
    error: null,
  };

  it('renders unsaved changes message', () => {
    render(<AgentSaveBar {...defaultProps} />);
    expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
  });

  it('renders Save and Discard buttons', () => {
    render(<AgentSaveBar {...defaultProps} />);
    expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Discard unsaved changes' })).toBeInTheDocument();
  });

  it('calls onSave when Save is clicked', async () => {
    const onSave = vi.fn();
    render(<AgentSaveBar {...defaultProps} onSave={onSave} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Save changes' }));
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  it('calls onDiscard when Discard is clicked', async () => {
    const onDiscard = vi.fn();
    render(<AgentSaveBar {...defaultProps} onDiscard={onDiscard} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Discard unsaved changes' }));
    expect(onDiscard).toHaveBeenCalledTimes(1);
  });

  it('shows Saving... text during save', () => {
    render(<AgentSaveBar {...defaultProps} isSaving={true} />);
    expect(screen.getByRole('button', { name: 'Saving changes' })).toBeDisabled();
  });

  it('disables buttons while saving', () => {
    render(<AgentSaveBar {...defaultProps} isSaving={true} />);
    expect(screen.getByRole('button', { name: 'Saving changes' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Discard unsaved changes' })).toBeDisabled();
  });

  it('shows error message when present', () => {
    render(<AgentSaveBar {...defaultProps} error="Failed to save configuration" />);
    expect(screen.getByText(/Failed to save configuration/)).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<AgentSaveBar {...defaultProps} />);
    await expectNoA11yViolations(container);
  });
});
