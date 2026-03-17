import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';

const mockBlocker = { state: 'unblocked', proceed: vi.fn(), reset: vi.fn() };

vi.mock('react-router-dom', () => ({
  useBlocker: vi.fn(() => mockBlocker),
}));

import { useBlocker } from 'react-router-dom';
import { useUnsavedChanges } from './useUnsavedChanges';

const mockUseBlocker = useBlocker as ReturnType<typeof vi.fn>;

describe('useUnsavedChanges', () => {
  let addEventSpy: ReturnType<typeof vi.spyOn>;
  let removeEventSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBlocker.mockReturnValue(mockBlocker);
    addEventSpy = vi.spyOn(window, 'addEventListener');
    removeEventSpy = vi.spyOn(window, 'removeEventListener');
  });

  afterEach(() => {
    addEventSpy.mockRestore();
    removeEventSpy.mockRestore();
  });

  it('does not block when isDirty is false', () => {
    const { result } = renderHook(() => useUnsavedChanges({ isDirty: false }));

    expect(result.current.isBlocked).toBe(false);
    expect(mockUseBlocker).toHaveBeenCalledWith(false);
  });

  it('activates blocker when isDirty is true', () => {
    mockUseBlocker.mockReturnValue({ state: 'blocked', proceed: vi.fn(), reset: vi.fn() });

    const { result } = renderHook(() => useUnsavedChanges({ isDirty: true }));

    expect(mockUseBlocker).toHaveBeenCalledWith(true);
    expect(result.current.isBlocked).toBe(true);
  });

  it('registers beforeunload handler when dirty', () => {
    renderHook(() => useUnsavedChanges({ isDirty: true }));

    expect(addEventSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
  });

  it('does not register beforeunload handler when clean', () => {
    renderHook(() => useUnsavedChanges({ isDirty: false }));

    const beforeUnloadCalls = addEventSpy.mock.calls.filter(
      ([event]) => event === 'beforeunload'
    );
    expect(beforeUnloadCalls).toHaveLength(0);
  });

  it('removes beforeunload handler on cleanup', () => {
    const { unmount } = renderHook(() => useUnsavedChanges({ isDirty: true }));

    unmount();

    expect(removeEventSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
  });

  it('returns blocker object', () => {
    const { result } = renderHook(() => useUnsavedChanges({ isDirty: false }));
    expect(result.current.blocker).toBeDefined();
    expect(result.current.blocker.state).toBe('unblocked');
  });

  it('uses custom message option', () => {
    renderHook(() =>
      useUnsavedChanges({ isDirty: true, message: 'Custom warning' })
    );

    // The beforeunload handler is registered — we verify it was set up
    expect(addEventSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
  });

  it('beforeunload handler sets returnValue', () => {
    renderHook(() => useUnsavedChanges({ isDirty: true }));

    const handler = addEventSpy.mock.calls.find(
      ([event]) => event === 'beforeunload'
    )?.[1] as EventListener;

    const event = new Event('beforeunload') as BeforeUnloadEvent;
    Object.defineProperty(event, 'preventDefault', { value: vi.fn() });

    handler(event);

    expect(event.returnValue).toBeTruthy();
  });
});
