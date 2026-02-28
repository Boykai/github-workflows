/**
 * Unit tests for useSettingsForm hook
 */
import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSettingsForm } from './useSettingsForm';

interface TestSettings {
  theme: string;
  language: string;
  notifications: boolean;
}

const defaultServerState: TestSettings = {
  theme: 'light',
  language: 'en',
  notifications: true,
};

describe('useSettingsForm', () => {
  it('should initialize localState from serverState', () => {
    const { result } = renderHook(() => useSettingsForm(defaultServerState));

    expect(result.current.localState).toEqual(defaultServerState);
  });

  it('should not be dirty initially', () => {
    const { result } = renderHook(() => useSettingsForm(defaultServerState));

    expect(result.current.isDirty).toBe(false);
  });

  it('setField should update a field in localState', () => {
    const { result } = renderHook(() => useSettingsForm(defaultServerState));

    act(() => {
      result.current.setField('theme', 'dark');
    });

    expect(result.current.localState.theme).toBe('dark');
    expect(result.current.localState.language).toBe('en');
  });

  it('setField should mark form as dirty', () => {
    const { result } = renderHook(() => useSettingsForm(defaultServerState));

    act(() => {
      result.current.setField('theme', 'dark');
    });

    expect(result.current.isDirty).toBe(true);
  });

  it('reset should revert to serverState', () => {
    const { result } = renderHook(() => useSettingsForm(defaultServerState));

    act(() => {
      result.current.setField('theme', 'dark');
      result.current.setField('language', 'fr');
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.localState).toEqual(defaultServerState);
  });

  it('reset should mark form as not dirty', () => {
    const { result } = renderHook(() => useSettingsForm(defaultServerState));

    act(() => {
      result.current.setField('theme', 'dark');
    });

    expect(result.current.isDirty).toBe(true);

    act(() => {
      result.current.reset();
    });

    expect(result.current.isDirty).toBe(false);
  });

  it('should re-sync when serverState changes', () => {
    const { result, rerender } = renderHook(
      ({ serverState }) => useSettingsForm(serverState),
      { initialProps: { serverState: defaultServerState } },
    );

    expect(result.current.localState.theme).toBe('light');

    const updatedServerState: TestSettings = {
      theme: 'dark',
      language: 'en',
      notifications: false,
    };

    rerender({ serverState: updatedServerState });

    expect(result.current.localState).toEqual(updatedServerState);
    expect(result.current.isDirty).toBe(false);
  });
});
