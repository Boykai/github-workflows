/**
 * Component tests for VoiceInputButton visual states and interactions.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { VoiceInputButton } from './VoiceInputButton';

describe('VoiceInputButton', () => {
  // ── Unsupported state ──

  it('renders disabled button with MicOff icon when unsupported', () => {
    render(
      <VoiceInputButton
        isSupported={false}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-label', 'Voice input not supported');
  });

  it('does not call onToggle when unsupported button is clicked', () => {
    const onToggle = vi.fn();
    render(
      <VoiceInputButton
        isSupported={false}
        isRecording={false}
        onToggle={onToggle}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(onToggle).not.toHaveBeenCalled();
  });

  it('applies cursor-not-allowed styling when unsupported', () => {
    render(
      <VoiceInputButton
        isSupported={false}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).toContain('cursor-not-allowed');
  });

  // ── Recording state ──

  it('renders stop button with correct aria-label when recording', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={true}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute('aria-label', 'Stop recording');
  });

  it('calls onToggle when recording button is clicked', () => {
    const onToggle = vi.fn();
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={true}
        onToggle={onToggle}
        error={null}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it('applies mic-recording-pulse animation when recording', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={true}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).toContain('mic-recording-pulse');
  });

  it('applies destructive styling when recording', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={true}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).toContain('bg-destructive/10');
    expect(button.className).toContain('text-destructive');
  });

  // ── Ready/idle state ──

  it('renders mic button with correct aria-label when ready', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute('aria-label', 'Start voice input');
  });

  it('calls onToggle when ready button is clicked', () => {
    const onToggle = vi.fn();
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={onToggle}
        error={null}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  // ── Error state ──

  it('applies destructive text color when error is present', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={vi.fn()}
        error="Microphone access denied"
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).toContain('text-destructive');
  });

  it('shows retry aria-label when error is present', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={vi.fn()}
        error="Microphone access denied"
      />
    );

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Voice input error — click to retry');
  });

  it('calls onToggle when error state button is clicked (retry)', () => {
    const onToggle = vi.fn();
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={onToggle}
        error="Microphone access denied"
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it('does not have a title attribute on the disabled unsupported button', () => {
    render(
      <VoiceInputButton
        isSupported={false}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button).not.toHaveAttribute('title');
  });

  it('does not apply destructive styling in idle state without error', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).not.toContain('text-destructive');
  });

  it('does not apply mic-recording-pulse in idle state', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).not.toContain('mic-recording-pulse');
  });

  // ── Accessibility ──

  it('applies celestial-focus class on recording button', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={true}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).toContain('celestial-focus');
  });

  it('applies celestial-focus class on ready button', () => {
    render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).toContain('celestial-focus');
  });

  it('does not apply celestial-focus class on disabled button', () => {
    render(
      <VoiceInputButton
        isSupported={false}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );

    const button = screen.getByRole('button');
    expect(button.className).not.toContain('celestial-focus');
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <VoiceInputButton
        isSupported={true}
        isRecording={false}
        onToggle={vi.fn()}
        error={null}
      />
    );
    await expectNoA11yViolations(container);
  });
});
