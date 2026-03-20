import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

import { useGlobalShortcuts } from './useGlobalShortcuts';

function fireKey(key: string, options: Partial<KeyboardEventInit> = {}) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, ...options });
  document.dispatchEvent(event);
  return event;
}

function fireKeyOnElement(
  element: HTMLElement,
  key: string,
  options: Partial<KeyboardEventInit> = {},
) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, ...options });
  element.dispatchEvent(event);
}

describe('useGlobalShortcuts', () => {
  let onOpenShortcutModal: ReturnType<typeof vi.fn>;
  let dispatchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();
    onOpenShortcutModal = vi.fn();
    dispatchSpy = vi.spyOn(window, 'dispatchEvent');
  });

  afterEach(() => {
    dispatchSpy.mockRestore();
    // Remove any modal dialogs left from tests
    document.querySelectorAll('[role="dialog"]').forEach((el) => el.remove());
  });

  function setup() {
    return renderHook(() => useGlobalShortcuts({ onOpenShortcutModal }));
  }

  it('opens shortcut modal on "?" key', () => {
    setup();
    fireKey('?');
    expect(onOpenShortcutModal).toHaveBeenCalledTimes(1);
  });

  it('navigates to sections on number keys 1-5', () => {
    setup();
    fireKey('1');
    expect(mockNavigate).toHaveBeenCalledWith('/');
    fireKey('2');
    expect(mockNavigate).toHaveBeenCalledWith('/board');
    fireKey('3');
    expect(mockNavigate).toHaveBeenCalledWith('/agents');
    fireKey('4');
    expect(mockNavigate).toHaveBeenCalledWith('/pipeline');
    fireKey('5');
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
  });

  it('dispatches solune:open-command-palette on Ctrl+K', () => {
    setup();
    fireKey('k', { ctrlKey: true });
    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(CustomEvent));
    const call = dispatchSpy.mock.calls.find(
      (c) => c[0] instanceof CustomEvent && c[0].type === 'solune:open-command-palette',
    );
    expect(call).toBeTruthy();
  });

  it('dispatches solune:open-command-palette on Meta+K (Mac)', () => {
    setup();
    fireKey('k', { metaKey: true });
    const call = dispatchSpy.mock.calls.find(
      (c) => c[0] instanceof CustomEvent && c[0].type === 'solune:open-command-palette',
    );
    expect(call).toBeTruthy();
  });

  it('does not fire shortcuts when focused on a text input', () => {
    setup();
    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    fireKeyOnElement(input, '?');
    expect(onOpenShortcutModal).not.toHaveBeenCalled();

    fireKeyOnElement(input, '1');
    expect(mockNavigate).not.toHaveBeenCalled();

    document.body.removeChild(input);
  });

  it('does not fire shortcuts when focused on a textarea', () => {
    setup();
    const textarea = document.createElement('textarea');
    document.body.appendChild(textarea);
    textarea.focus();

    fireKeyOnElement(textarea, '2');
    expect(mockNavigate).not.toHaveBeenCalled();

    document.body.removeChild(textarea);
  });

  it('suppresses non-Escape shortcuts when a modal dialog is open', () => {
    setup();
    // Create a modal dialog element
    const dialog = document.createElement('div');
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    document.body.appendChild(dialog);

    fireKey('?');
    expect(onOpenShortcutModal).not.toHaveBeenCalled();

    fireKey('1');
    expect(mockNavigate).not.toHaveBeenCalled();

    document.body.removeChild(dialog);
  });

  it('does not dispatch command palette event when a modal dialog is open', () => {
    setup();
    const dialog = document.createElement('div');
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    document.body.appendChild(dialog);

    fireKey('k', { ctrlKey: true });
    const call = dispatchSpy.mock.calls.find(
      (c) => c[0] instanceof CustomEvent && c[0].type === 'solune:open-command-palette',
    );
    expect(call).toBeFalsy();

    document.body.removeChild(dialog);
  });

  it('cleans up event listener on unmount', () => {
    const addSpy = vi.spyOn(document, 'addEventListener');
    const removeSpy = vi.spyOn(document, 'removeEventListener');

    const { unmount } = setup();
    expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function));

    unmount();
    expect(removeSpy).toHaveBeenCalledWith('keydown', expect.any(Function));

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });
});
