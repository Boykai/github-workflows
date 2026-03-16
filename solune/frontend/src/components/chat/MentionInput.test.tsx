import { createRef, type ComponentProps } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

import { MentionInput, type MentionInputHandle } from './MentionInput';

describe('MentionInput', () => {
  function renderMentionInput(overrides: Partial<ComponentProps<typeof MentionInput>> = {}) {
    const ref = createRef<MentionInputHandle>();
    const props: ComponentProps<typeof MentionInput> = {
      value: '',
      placeholder: 'Type a message',
      disabled: false,
      isNavigating: false,
      onTextChange: vi.fn(),
      onTokenRemove: vi.fn(),
      onMentionTrigger: vi.fn(),
      onMentionDismiss: vi.fn(),
      onSubmit: vi.fn(),
      onKeyDown: vi.fn(),
      ...overrides,
    };

    return {
      ref,
      props,
      ...render(<MentionInput ref={ref} {...props} />),
    };
  }

  it('reflects programmatic value updates in the editor', () => {
    const { rerender, props } = renderMentionInput({ value: 'Initial text' });

    expect(screen.getByRole('textbox')).toHaveTextContent('Initial text');

    rerender(<MentionInput {...props} value="Updated from history" />);

    expect(screen.getByRole('textbox')).toHaveTextContent('Updated from history');
  });

  it('renders the placeholder when value is empty', () => {
    renderMentionInput({ value: '', placeholder: 'Ask anything' });
    expect(screen.getByText('Ask anything')).toBeInTheDocument();
  });

  it('uses custom ariaLabel when provided', () => {
    renderMentionInput({ ariaLabel: 'Custom chat label' });
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-label', 'Custom chat label');
  });

  it('falls back to default aria-label when ariaLabel is not provided', () => {
    renderMentionInput();
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-label', 'Chat input');
  });

  it('renders mobile placeholder variant when placeholderMobile is provided', () => {
    const { container } = renderMentionInput({
      placeholder: 'Desktop placeholder',
      placeholderMobile: 'Mobile placeholder',
    });

    expect(screen.getByText('Desktop placeholder')).toBeInTheDocument();
    expect(screen.getByText('Mobile placeholder')).toBeInTheDocument();

    // Desktop span should have max-sm:hidden class
    const desktopSpan = container.querySelector('.max-sm\\:hidden');
    expect(desktopSpan).toHaveTextContent('Desktop placeholder');

    // Mobile span should have hidden max-sm:inline classes
    const mobileSpan = screen.getByText('Mobile placeholder');
    expect(mobileSpan.className).toContain('max-sm:inline');
  });

  it('renders cycling placeholder when provided', () => {
    renderMentionInput({
      placeholder: 'Static text',
      placeholderMobile: 'Mobile text',
      cyclingPlaceholder: 'Try: summarize issues',
    });

    expect(screen.getByText('Try: summarize issues')).toBeInTheDocument();
  });

  it('renders cycling placeholder without requiring a mobile placeholder', () => {
    renderMentionInput({
      placeholder: 'Static text',
      cyclingPlaceholder: 'Try: summarize issues',
    });

    expect(screen.getByText('Try: summarize issues')).toBeInTheDocument();
  });

  it('applies motion-reduce:animate-none class to cycling placeholder span', () => {
    renderMentionInput({
      placeholder: 'Static text',
      placeholderMobile: 'Mobile text',
      cyclingPlaceholder: 'Try: summarize issues',
    });

    const cyclingSpan = screen.getByText('Try: summarize issues');
    expect(cyclingSpan.className).toContain('motion-reduce:animate-none');
  });

  it('does not render placeholder when disabled', () => {
    renderMentionInput({ placeholder: 'Type here', disabled: true });
    expect(screen.queryByText('Type here')).not.toBeInTheDocument();
  });

  it('removes mention tokens from hook state when backspacing over a token', () => {
    const onTextChange = vi.fn();
    const onTokenRemove = vi.fn();
    const { ref } = renderMentionInput({ onTextChange, onTokenRemove });
    const textbox = screen.getByRole('textbox');

    textbox.textContent = '@pl';
    const selection = window.getSelection();
    const range = document.createRange();
    range.setStart(textbox.firstChild as Text, 3);
    range.collapse(true);
    selection?.removeAllRanges();
    selection?.addRange(range);

    act(() => {
      ref.current?.insertTokenAtCursor('pipe-1', 'Platform', 0, 2);
    });

    const postInsertRange = document.createRange();
    postInsertRange.setStart(textbox, 2);
    postInsertRange.collapse(true);
    selection?.removeAllRanges();
    selection?.addRange(postInsertRange);

    act(() => {
      fireEvent.keyDown(textbox, { key: 'Backspace' });
    });

    expect(onTokenRemove).toHaveBeenCalledWith('pipe-1');
    expect(onTextChange).toHaveBeenLastCalledWith('');
    expect(textbox.querySelector('[data-mention-token]')).toBeNull();
  });

  it('has no accessibility violations', async () => {
    const { container } = renderMentionInput();
    await expectNoA11yViolations(container);
  });
});
