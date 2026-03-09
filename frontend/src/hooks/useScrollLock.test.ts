/**
 * Unit tests for useScrollLock hook — reference-counting scroll lock.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useScrollLock, _resetForTesting } from './useScrollLock';

describe('useScrollLock', () => {
  beforeEach(() => {
    _resetForTesting();
  });

  it('locks body overflow when isLocked is true', () => {
    renderHook(() => useScrollLock(true));
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('does not lock body overflow when isLocked is false', () => {
    document.body.style.overflow = 'auto';
    renderHook(() => useScrollLock(false));
    expect(document.body.style.overflow).toBe('auto');
  });

  it('restores original overflow on unmount', () => {
    document.body.style.overflow = 'auto';
    const { unmount } = renderHook(() => useScrollLock(true));
    expect(document.body.style.overflow).toBe('hidden');
    unmount();
    expect(document.body.style.overflow).toBe('auto');
  });

  it('restores empty string when original overflow was empty', () => {
    document.body.style.overflow = '';
    const { unmount } = renderHook(() => useScrollLock(true));
    expect(document.body.style.overflow).toBe('hidden');
    unmount();
    expect(document.body.style.overflow).toBe('');
  });

  it('handles multiple concurrent locks via reference counting', () => {
    const hook1 = renderHook(() => useScrollLock(true));
    const hook2 = renderHook(() => useScrollLock(true));

    expect(document.body.style.overflow).toBe('hidden');

    // Unmounting the first lock should keep overflow hidden (second still active)
    hook1.unmount();
    expect(document.body.style.overflow).toBe('hidden');

    // Unmounting the second lock should restore overflow
    hook2.unmount();
    expect(document.body.style.overflow).toBe('');
  });

  it('handles closing inner modal before outer modal', () => {
    document.body.style.overflow = 'scroll';
    const outer = renderHook(() => useScrollLock(true));
    const inner = renderHook(() => useScrollLock(true));

    expect(document.body.style.overflow).toBe('hidden');

    inner.unmount();
    expect(document.body.style.overflow).toBe('hidden');

    outer.unmount();
    expect(document.body.style.overflow).toBe('scroll');
  });

  it('handles toggling isLocked from true to false', () => {
    document.body.style.overflow = '';
    const { rerender } = renderHook(({ locked }: { locked: boolean }) => useScrollLock(locked), {
      initialProps: { locked: true },
    });
    expect(document.body.style.overflow).toBe('hidden');

    act(() => {
      rerender({ locked: false });
    });
    expect(document.body.style.overflow).toBe('');
  });

  it('handles toggling isLocked from false to true', () => {
    document.body.style.overflow = '';
    const { rerender } = renderHook(({ locked }: { locked: boolean }) => useScrollLock(locked), {
      initialProps: { locked: false },
    });
    expect(document.body.style.overflow).toBe('');

    act(() => {
      rerender({ locked: true });
    });
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('handles rapid open/close sequences correctly', () => {
    const hook1 = renderHook(({ locked }: { locked: boolean }) => useScrollLock(locked), {
      initialProps: { locked: true },
    });
    expect(document.body.style.overflow).toBe('hidden');

    act(() => {
      hook1.rerender({ locked: false });
    });
    expect(document.body.style.overflow).toBe('');

    act(() => {
      hook1.rerender({ locked: true });
    });
    expect(document.body.style.overflow).toBe('hidden');

    act(() => {
      hook1.rerender({ locked: false });
    });
    expect(document.body.style.overflow).toBe('');
  });

  it('never lets lock count go negative (defensive guard)', () => {
    // Unmount without ever being locked should not cause issues
    const { unmount } = renderHook(() => useScrollLock(false));
    unmount();

    // Subsequent lock/unlock should still work correctly
    document.body.style.overflow = '';
    const hook = renderHook(() => useScrollLock(true));
    expect(document.body.style.overflow).toBe('hidden');
    hook.unmount();
    expect(document.body.style.overflow).toBe('');
  });
});

describe('useScrollLock — <main> scroll container targeting', () => {
  let mainEl: HTMLElement;

  beforeEach(() => {
    mainEl = document.createElement('main');
    document.body.appendChild(mainEl);
    _resetForTesting();
  });

  afterEach(() => {
    if (mainEl.isConnected) {
      document.body.removeChild(mainEl);
    }
  });

  it('locks <main> overflow (not body) when isLocked is true', () => {
    document.body.style.overflow = 'auto';
    renderHook(() => useScrollLock(true));
    expect(mainEl.style.overflow).toBe('hidden');
    expect(document.body.style.overflow).toBe('auto');
  });

  it('restores <main> overflow on unmount', () => {
    mainEl.style.overflow = 'auto';
    const { unmount } = renderHook(() => useScrollLock(true));
    expect(mainEl.style.overflow).toBe('hidden');
    unmount();
    expect(mainEl.style.overflow).toBe('auto');
  });

  it('handles reference counting on <main> with multiple consumers', () => {
    const hook1 = renderHook(() => useScrollLock(true));
    const hook2 = renderHook(() => useScrollLock(true));

    expect(mainEl.style.overflow).toBe('hidden');

    hook1.unmount();
    expect(mainEl.style.overflow).toBe('hidden');

    hook2.unmount();
    expect(mainEl.style.overflow).toBe('');
  });

  it('does not affect body overflow when <main> is the target', () => {
    document.body.style.overflow = 'scroll';
    const { unmount } = renderHook(() => useScrollLock(true));
    expect(mainEl.style.overflow).toBe('hidden');
    expect(document.body.style.overflow).toBe('scroll');
    unmount();
    expect(document.body.style.overflow).toBe('scroll');
  });

  it('restores the originally locked element when the scroll container changes', () => {
    mainEl.style.overflow = 'auto';
    const { unmount } = renderHook(() => useScrollLock(true));

    expect(mainEl.style.overflow).toBe('hidden');

    document.body.removeChild(mainEl);

    const replacementMain = document.createElement('main');
    document.body.appendChild(replacementMain);

    unmount();

    expect(mainEl.style.overflow).toBe('auto');
    expect(replacementMain.style.overflow).toBe('');

    document.body.removeChild(replacementMain);
  });
});
