import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useOnboarding, OnboardingProvider } from './useOnboarding';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <OnboardingProvider>{children}</OnboardingProvider>
);

describe('useOnboarding', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('auto-activates on first visit when no completion flag exists', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    expect(result.current.isActive).toBe(true);
    expect(result.current.hasCompleted).toBe(false);
    expect(result.current.currentStep).toBe(0);
    expect(result.current.totalSteps).toBe(14);
  });

  it('does not activate when completion flag exists', () => {
    localStorage.setItem('solune-onboarding-completed', 'true');
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    expect(result.current.isActive).toBe(false);
    expect(result.current.hasCompleted).toBe(true);
  });

  it('advances step on next()', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    act(() => result.current.next());
    expect(result.current.currentStep).toBe(1);
    act(() => result.current.next());
    expect(result.current.currentStep).toBe(2);
  });

  it('goes back on prev()', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    act(() => result.current.next());
    act(() => result.current.next());
    act(() => result.current.prev());
    expect(result.current.currentStep).toBe(1);
  });

  it('does not go below step 0 on prev()', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    act(() => result.current.prev());
    expect(result.current.currentStep).toBe(0);
  });

  it('completes tour when next() at last step', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    for (let i = 0; i < 13; i++) {
      act(() => result.current.next());
    }
    expect(result.current.currentStep).toBe(13);
    act(() => result.current.next());
    expect(result.current.isActive).toBe(false);
    expect(result.current.hasCompleted).toBe(true);
    expect(localStorage.getItem('solune-onboarding-completed')).toBe('true');
  });

  it('skip() sets completion flag and deactivates', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    act(() => result.current.next());
    act(() => result.current.skip());
    expect(result.current.isActive).toBe(false);
    expect(result.current.hasCompleted).toBe(true);
    expect(localStorage.getItem('solune-onboarding-completed')).toBe('true');
  });

  it('restart() resets to step 0 and activates without clearing hasCompleted', () => {
    const { result } = renderHook(() => useOnboarding(), { wrapper });
    act(() => result.current.skip());
    expect(result.current.hasCompleted).toBe(true);

    act(() => result.current.restart());
    expect(result.current.isActive).toBe(true);
    expect(result.current.currentStep).toBe(0);
    // hasCompleted remains true — replay doesn't reset the first-visit flag
    expect(result.current.hasCompleted).toBe(true);
  });

  it('persists completion across hook re-mounts', () => {
    const { result, unmount } = renderHook(() => useOnboarding(), { wrapper });
    act(() => result.current.skip());
    unmount();

    const { result: result2 } = renderHook(() => useOnboarding(), { wrapper });
    expect(result2.current.isActive).toBe(false);
    expect(result2.current.hasCompleted).toBe(true);
  });
});
