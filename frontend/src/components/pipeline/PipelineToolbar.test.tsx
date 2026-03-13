import { describe, expect, it, vi, beforeEach } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { PipelineToolbar } from './PipelineToolbar';
import type { PipelineBoardState, PipelineValidationErrors } from '@/types';

vi.mock('@/hooks/useScrollLock', () => ({
  useScrollLock: vi.fn(),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({
    children,
    disabled,
    onClick,
    variant,
  }: {
    children: React.ReactNode;
    disabled?: boolean;
    onClick?: () => void;
    variant?: string;
    size?: string;
  }) => (
    <button disabled={disabled} onClick={onClick} data-variant={variant}>
      {children}
    </button>
  ),
}));

const defaultProps = {
  boardState: 'editing' as PipelineBoardState,
  isDirty: false,
  isSaving: false,
  isPreset: false,
  pipelineName: 'My Pipeline',
  validationErrors: {} as PipelineValidationErrors,
  onSave: vi.fn(),
  onSaveAsCopy: vi.fn(),
  onDelete: vi.fn(),
  onDiscard: vi.fn(),
};

describe('PipelineToolbar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Save, Discard, and Delete buttons', () => {
    render(<PipelineToolbar {...defaultProps} />);
    expect(screen.getByText('Save')).toBeInTheDocument();
    expect(screen.getByText('Discard')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('enables Save when editing a non-preset', () => {
    render(<PipelineToolbar {...defaultProps} boardState="editing" isPreset={false} />);
    expect(screen.getByText('Save').closest('button')).not.toBeDisabled();
  });

  it('enables Save when creating', () => {
    render(<PipelineToolbar {...defaultProps} boardState="creating" />);
    expect(screen.getByText('Save').closest('button')).not.toBeDisabled();
  });

  it('disables Discard when not dirty', () => {
    render(<PipelineToolbar {...defaultProps} isDirty={false} />);
    expect(screen.getByText('Discard').closest('button')).toBeDisabled();
  });

  it('enables Discard when dirty', () => {
    render(<PipelineToolbar {...defaultProps} isDirty={true} />);
    expect(screen.getByText('Discard').closest('button')).not.toBeDisabled();
  });

  it('disables Delete for presets', () => {
    render(<PipelineToolbar {...defaultProps} isPreset={true} />);
    expect(screen.getByText('Delete').closest('button')).toBeDisabled();
  });

  it('enables Delete for non-preset editing', () => {
    render(<PipelineToolbar {...defaultProps} boardState="editing" isPreset={false} />);
    expect(screen.getByText('Delete').closest('button')).not.toBeDisabled();
  });

  it('shows "Save as Copy" button for presets in editing mode', () => {
    render(<PipelineToolbar {...defaultProps} boardState="editing" isPreset={true} />);
    expect(screen.getByText('Save as Copy')).toBeInTheDocument();
  });

  it('calls onSave when Save button is clicked', async () => {
    const { userEvent } = await import('@/test/test-utils');
    const user = userEvent.setup();
    render(<PipelineToolbar {...defaultProps} boardState="editing" isPreset={false} />);
    await user.click(screen.getByText('Save'));
    expect(defaultProps.onSave).toHaveBeenCalledOnce();
  });

  it('calls onDiscard when Discard button is clicked', async () => {
    const { userEvent } = await import('@/test/test-utils');
    const user = userEvent.setup();
    render(<PipelineToolbar {...defaultProps} isDirty={true} />);
    await user.click(screen.getByText('Discard'));
    expect(defaultProps.onDiscard).toHaveBeenCalledOnce();
  });

  it('calls onDelete when Delete button is clicked', async () => {
    const { userEvent } = await import('@/test/test-utils');
    const user = userEvent.setup();
    render(<PipelineToolbar {...defaultProps} boardState="editing" isPreset={false} />);
    await user.click(screen.getByText('Delete'));
    expect(defaultProps.onDelete).toHaveBeenCalledOnce();
  });
});
