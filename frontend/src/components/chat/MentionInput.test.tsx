import { createRef, type ComponentProps } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

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
});
