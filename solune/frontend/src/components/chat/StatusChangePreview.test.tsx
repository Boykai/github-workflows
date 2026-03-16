/**
 * Integration tests for StatusChangePreview — status change confirmation.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { StatusChangePreview } from './StatusChangePreview';

describe('StatusChangePreview', () => {
  const defaultProps = {
    taskTitle: 'Fix Login Bug',
    currentStatus: 'Todo',
    targetStatus: 'In Progress',
    onConfirm: vi.fn(),
    onReject: vi.fn(),
  };

  it('renders task title', () => {
    render(<StatusChangePreview {...defaultProps} />);
    expect(screen.getByText('Fix Login Bug')).toBeInTheDocument();
  });

  it('renders current and target status', () => {
    render(<StatusChangePreview {...defaultProps} />);
    expect(screen.getByText('Todo')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('→')).toBeInTheDocument();
  });

  it('renders Status Change header', () => {
    render(<StatusChangePreview {...defaultProps} />);
    expect(screen.getByText('Status Change')).toBeInTheDocument();
  });

  it('calls onConfirm when Update Status is clicked', async () => {
    const onConfirm = vi.fn();
    render(<StatusChangePreview {...defaultProps} onConfirm={onConfirm} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Update Status' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onReject when Cancel is clicked', async () => {
    const onReject = vi.fn();
    render(<StatusChangePreview {...defaultProps} onReject={onReject} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onReject).toHaveBeenCalledTimes(1);
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<StatusChangePreview {...defaultProps} />);
    await expectNoA11yViolations(container);
  });
});
