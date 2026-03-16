/**
 * Tests for ConfirmationDialog component.
 *
 * Covers: variant rendering (danger/warning/info), confirm/cancel actions,
 * Escape key dismissal, backdrop click, loading state, error display,
 * and ARIA accessibility attributes.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmationDialog, type ConfirmationDialogProps } from '../confirmation-dialog';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

function renderDialog(overrides: Partial<ConfirmationDialogProps> = {}) {
  const defaultProps: ConfirmationDialogProps = {
    isOpen: true,
    title: 'Delete Item',
    description: 'Are you sure you want to delete this item?',
    variant: 'danger',
    confirmLabel: 'Delete',
    cancelLabel: 'Cancel',
    isLoading: false,
    error: null,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    ...overrides,
  };

  return { ...render(<ConfirmationDialog {...defaultProps} />), props: defaultProps };
}

describe('ConfirmationDialog', () => {
  it('renders nothing when isOpen is false', () => {
    renderDialog({ isOpen: false });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders the dialog when isOpen is true', () => {
    renderDialog();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to delete this item?')).toBeInTheDocument();
  });

  it('renders custom title, description, and button labels', () => {
    renderDialog({
      title: 'Custom Title',
      description: 'Custom description text',
      confirmLabel: 'Yes, do it',
      cancelLabel: 'Nope',
    });
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
    expect(screen.getByText('Custom description text')).toBeInTheDocument();
    expect(screen.getByText('Yes, do it')).toBeInTheDocument();
    expect(screen.getByText('Nope')).toBeInTheDocument();
  });

  // Variant rendering
  it('renders danger variant with AlertTriangle icon', () => {
    renderDialog({ variant: 'danger' });
    const dialog = screen.getByRole('dialog');
    // Danger variant should show the icon with red styling
    const icon = dialog.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('renders warning variant', () => {
    renderDialog({ variant: 'warning' });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
  });

  it('renders info variant', () => {
    renderDialog({ variant: 'info' });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
  });

  // Actions
  it('calls onConfirm when confirm button is clicked', () => {
    const { props } = renderDialog();
    fireEvent.click(screen.getByText('Delete'));
    expect(props.onConfirm).toHaveBeenCalledOnce();
  });

  it('calls onCancel when cancel button is clicked', () => {
    const { props } = renderDialog();
    fireEvent.click(screen.getByText('Cancel'));
    expect(props.onCancel).toHaveBeenCalledOnce();
  });

  it('calls onCancel when Escape key is pressed', () => {
    const { props } = renderDialog();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(props.onCancel).toHaveBeenCalledOnce();
  });

  it('calls onCancel when backdrop is clicked', () => {
    const { props } = renderDialog();
    // The backdrop is the first child div with bg-black/50
    const backdrop = screen
      .getByRole('dialog')
      .parentElement!.querySelector('[aria-hidden="true"]')!;
    fireEvent.click(backdrop);
    expect(props.onCancel).toHaveBeenCalledOnce();
  });

  // Loading state
  it('disables both buttons during loading state', () => {
    renderDialog({ isLoading: true });
    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it('shows "Processing…" text during loading state', () => {
    renderDialog({ isLoading: true });
    expect(screen.getByText('Processing…')).toBeInTheDocument();
  });

  it('does not call onCancel on Escape during loading state', () => {
    const { props } = renderDialog({ isLoading: true });
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(props.onCancel).not.toHaveBeenCalled();
  });

  it('does not call onCancel on backdrop click during loading state', () => {
    const { props } = renderDialog({ isLoading: true });
    const backdrop = screen
      .getByRole('dialog')
      .parentElement!.querySelector('[aria-hidden="true"]')!;
    fireEvent.click(backdrop);
    expect(props.onCancel).not.toHaveBeenCalled();
  });

  // Error state
  it('displays error message when error prop is set', () => {
    renderDialog({ error: 'Network error occurred' });
    expect(screen.getByText('Network error occurred')).toBeInTheDocument();
  });

  it('does not display error message when error is null', () => {
    renderDialog({ error: null });
    expect(screen.queryByText('Network error occurred')).not.toBeInTheDocument();
  });

  // Accessibility
  it('has role="dialog" and aria-modal="true"', () => {
    renderDialog();
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('has aria-labelledby referencing the title', () => {
    renderDialog();
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-labelledby', 'confirmation-dialog-title');
    const title = document.getElementById('confirmation-dialog-title');
    expect(title).toHaveTextContent('Delete Item');
  });

  it('has aria-describedby referencing the description', () => {
    renderDialog();
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-describedby', 'confirmation-dialog-description');
    const desc = document.getElementById('confirmation-dialog-description');
    expect(desc).toHaveTextContent('Are you sure you want to delete this item?');
  });

  it('has no accessibility violations', async () => {
    const { container } = renderDialog();
    await expectNoA11yViolations(container);
  });
});
