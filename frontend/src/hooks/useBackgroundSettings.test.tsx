/**
 * Unit tests for useBackgroundSettings hook
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useBackgroundSettings, PRESET_BACKGROUNDS } from './useBackgroundSettings';

describe('useBackgroundSettings', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should initialize with default background', () => {
    const { result } = renderHook(() => useBackgroundSettings());

    expect(result.current.background).toEqual({
      type: 'default',
      value: 'var(--color-bg)',
    });
  });

  it('should load background from localStorage on mount', () => {
    const storedBackground = {
      type: 'preset',
      value: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    };
    localStorage.setItem('chat_background_settings', JSON.stringify(storedBackground));

    const { result } = renderHook(() => useBackgroundSettings());

    expect(result.current.background).toEqual(storedBackground);
  });

  it('should handle invalid JSON in localStorage gracefully', () => {
    localStorage.setItem('chat_background_settings', 'invalid-json');

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { result } = renderHook(() => useBackgroundSettings());

    expect(result.current.background).toEqual({
      type: 'default',
      value: 'var(--color-bg)',
    });
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('should set preset background', () => {
    const { result } = renderHook(() => useBackgroundSettings());

    act(() => {
      result.current.setPresetBackground('linear-gradient(135deg, #667eea 0%, #764ba2 100%)');
    });

    expect(result.current.background).toEqual({
      type: 'preset',
      value: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    });

    // Verify localStorage is updated
    const stored = localStorage.getItem('chat_background_settings');
    expect(stored).toBeTruthy();
    expect(JSON.parse(stored!)).toEqual({
      type: 'preset',
      value: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    });
  });

  it('should set custom background', () => {
    const { result } = renderHook(() => useBackgroundSettings());
    const mockDataUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

    act(() => {
      result.current.setCustomBackground(mockDataUrl);
    });

    expect(result.current.background).toEqual({
      type: 'custom',
      value: mockDataUrl,
    });

    // Verify localStorage is updated
    const stored = localStorage.getItem('chat_background_settings');
    expect(stored).toBeTruthy();
    expect(JSON.parse(stored!)).toEqual({
      type: 'custom',
      value: mockDataUrl,
    });
  });

  it('should reset to default background', () => {
    const { result } = renderHook(() => useBackgroundSettings());

    // First set a custom background
    act(() => {
      result.current.setPresetBackground('linear-gradient(135deg, #667eea 0%, #764ba2 100%)');
    });

    expect(result.current.background.type).toBe('preset');

    // Then reset
    act(() => {
      result.current.resetToDefault();
    });

    expect(result.current.background).toEqual({
      type: 'default',
      value: 'var(--color-bg)',
    });

    // Verify localStorage is updated
    const stored = localStorage.getItem('chat_background_settings');
    expect(stored).toBeTruthy();
    expect(JSON.parse(stored!)).toEqual({
      type: 'default',
      value: 'var(--color-bg)',
    });
  });

  it('should persist background settings across hook remounts', () => {
    const { result: result1 } = renderHook(() => useBackgroundSettings());

    act(() => {
      result1.current.setPresetBackground('linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)');
    });

    // Unmount and remount the hook
    const { result: result2 } = renderHook(() => useBackgroundSettings());

    expect(result2.current.background).toEqual({
      type: 'preset',
      value: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    });
  });

  describe('PRESET_BACKGROUNDS', () => {
    it('should have at least 5 preset backgrounds', () => {
      expect(PRESET_BACKGROUNDS.length).toBeGreaterThanOrEqual(5);
    });

    it('should have unique IDs for each preset', () => {
      const ids = PRESET_BACKGROUNDS.map(preset => preset.id);
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(ids.length);
    });

    it('should have names for all presets', () => {
      PRESET_BACKGROUNDS.forEach(preset => {
        expect(preset.name).toBeTruthy();
        expect(typeof preset.name).toBe('string');
        expect(preset.name.length).toBeGreaterThan(0);
      });
    });

    it('should have CSS gradient values for all presets', () => {
      PRESET_BACKGROUNDS.forEach(preset => {
        expect(preset.value).toBeTruthy();
        expect(typeof preset.value).toBe('string');
        expect(preset.value).toContain('gradient');
      });
    });

    it('should include specific preset backgrounds', () => {
      const presetNames = PRESET_BACKGROUNDS.map(p => p.name);
      expect(presetNames).toContain('Ocean Blue');
      expect(presetNames).toContain('Sunset');
      expect(presetNames).toContain('Forest');
      expect(presetNames).toContain('Purple Dream');
      expect(presetNames).toContain('Dark Mode');
    });
  });
});
