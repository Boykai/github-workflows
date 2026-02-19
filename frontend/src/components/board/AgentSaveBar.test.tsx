/**
 * Unit tests for AgentSaveBar component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentSaveBar } from './AgentSaveBar';

function renderBar(overrides: Partial<Parameters<typeof AgentSaveBar>[0]> = {}) {
  const props = {
    onSave: vi.fn(),
    onDiscard: vi.fn(),
    isSaving: false,
    error: null,
    ...overrides,
  };
  const result = render(<AgentSaveBar {...props} />);
  return { ...result, props };
}

describe('AgentSaveBar', () => {
  it('renders "You have unsaved changes" label', () => {
    renderBar();
    expect(screen.getByText('You have unsaved changes')).toBeDefined();
  });

  it('Save button calls onSave', () => {
    const { props } = renderBar();
    fireEvent.click(screen.getByText('Save'));
    expect(props.onSave).toHaveBeenCalledOnce();
  });

  it('Discard button calls onDiscard', () => {
    const { props } = renderBar();
    fireEvent.click(screen.getByText('Discard'));
    expect(props.onDiscard).toHaveBeenCalledOnce();
  });

  it('buttons are disabled when isSaving', () => {
    renderBar({ isSaving: true });
    expect(screen.getByText('Saving...').closest('button')!.disabled).toBe(true);
    expect(screen.getByText('Discard').closest('button')!.disabled).toBe(true);
  });

  it('shows "Saving..." text when isSaving', () => {
    renderBar({ isSaving: true });
    expect(screen.getByText('Saving...')).toBeDefined();
    expect(screen.queryByText('Save')).toBeNull();
  });

  it('shows error message when error prop is provided', () => {
    renderBar({ error: 'Network failure' });
    expect(screen.getByText('⚠ Network failure')).toBeDefined();
  });
});
