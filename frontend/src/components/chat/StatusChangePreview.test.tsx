/**
 * Unit tests for StatusChangePreview component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { StatusChangePreview } from './StatusChangePreview';

describe('StatusChangePreview', () => {
  const defaultProps = {
    taskTitle: 'Fix login bug',
    currentStatus: 'To Do',
    targetStatus: 'In Progress',
    onConfirm: vi.fn(),
    onReject: vi.fn(),
  };

  it('renders task title, current and target status', () => {
    render(<StatusChangePreview {...defaultProps} />);
    expect(screen.getByText('Fix login bug')).toBeDefined();
    expect(screen.getByText('To Do')).toBeDefined();
    expect(screen.getByText('In Progress')).toBeDefined();
  });

  it('shows status arrow between badges', () => {
    render(<StatusChangePreview {...defaultProps} />);
    expect(screen.getByText('→')).toBeDefined();
  });

  it('renders Status Change label', () => {
    render(<StatusChangePreview {...defaultProps} />);
    expect(screen.getByText('Status Change')).toBeDefined();
  });

  it('calls onConfirm when Update Status button clicked', () => {
    const onConfirm = vi.fn();
    render(<StatusChangePreview {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText('Update Status'));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('calls onReject when Cancel button clicked', () => {
    const onReject = vi.fn();
    render(<StatusChangePreview {...defaultProps} onReject={onReject} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onReject).toHaveBeenCalledOnce();
  });

  it('applies status CSS classes based on status names', () => {
    const { container } = render(<StatusChangePreview {...defaultProps} />);
    expect(container.querySelector('.status-to-do')).not.toBeNull();
    expect(container.querySelector('.status-in-progress')).not.toBeNull();
  });
});
