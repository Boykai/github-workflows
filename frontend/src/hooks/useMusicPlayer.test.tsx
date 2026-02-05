/**
 * Tests for useMusicPlayer hook.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMusicPlayer } from './useMusicPlayer';

describe('useMusicPlayer', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should initialize with saved preference from localStorage', () => {
    localStorage.setItem('gh-projects-bgm-state', 'silent');
    
    const { result } = renderHook(() => useMusicPlayer());
    
    expect(result.current.soundSilenced).toBe(true);
  });

  it('should initialize with audible state when no preference saved', () => {
    const { result } = renderHook(() => useMusicPlayer());
    
    expect(result.current.soundSilenced).toBe(false);
  });

  it('should toggle sound state', () => {
    const { result } = renderHook(() => useMusicPlayer());
    
    expect(result.current.soundSilenced).toBe(false);
    
    act(() => {
      result.current.toggleSound();
    });
    
    expect(result.current.soundSilenced).toBe(true);
  });

  it('should persist preference to localStorage on toggle', () => {
    const { result } = renderHook(() => useMusicPlayer());
    
    act(() => {
      result.current.toggleSound();
    });
    
    expect(localStorage.getItem('gh-projects-bgm-state')).toBe('silent');
    
    act(() => {
      result.current.toggleSound();
    });
    
    expect(localStorage.getItem('gh-projects-bgm-state')).toBe('audible');
  });

  it('should start with playback inactive', () => {
    const { result } = renderHook(() => useMusicPlayer());
    
    expect(result.current.playbackActive).toBe(false);
  });
});
