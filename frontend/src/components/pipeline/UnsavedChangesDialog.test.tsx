import { describe, expect, it, vi, beforeEach } from 'vitest';
import { screen, render } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { UnsavedChangesDialog } from './UnsavedChangesDialog';

vi.mock('@/components/ui/button', () => ({
  Button: ({
    children,
    onClick,
    variant,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    variant?: string;
  }) => (
    <button onClick={onClick} data-variant={variant}>
      {children}
    </button>
  ),
}));

const defaultProps = {
  isOpen: true,
  onSave: vi.fn(),
  onDiscard: vi.fn(),
  onCancel: vi.fn(),
};

describe('UnsavedChangesDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns null when not open', () => {
    const { container } = render(<UnsavedChangesDialog {...defaultProps} isOpen={false} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders "Unsaved Changes" heading when open', () => {
    render(<UnsavedChangesDialog {...defaultProps} />);
    expect(screen.getByText('Unsaved Changes')).toBeInTheDocument();
  });

  it('shows action description when provided', () => {
    render(<UnsavedChangesDialog {...defaultProps} actionDescription="navigate away" />);
    expect(screen.getByText(/navigate away/)).toBeInTheDocument();
  });

  it('calls onCancel when Cancel is clicked', async () => {
    const user = userEvent.setup();
    render(<UnsavedChangesDialog {...defaultProps} />);
    await user.click(screen.getByText('Cancel'));
    expect(defaultProps.onCancel).toHaveBeenCalledOnce();
  });

  it('calls onDiscard when Discard is clicked', async () => {
    const user = userEvent.setup();
    render(<UnsavedChangesDialog {...defaultProps} />);
    await user.click(screen.getByText('Discard'));
    expect(defaultProps.onDiscard).toHaveBeenCalledOnce();
  });

  it('calls onSave when Save Changes is clicked', async () => {
    const user = userEvent.setup();
    render(<UnsavedChangesDialog {...defaultProps} />);
    await user.click(screen.getByText('Save Changes'));
    expect(defaultProps.onSave).toHaveBeenCalledOnce();
  });
});
