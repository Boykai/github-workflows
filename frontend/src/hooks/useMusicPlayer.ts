/**
 * Background elevator music control hook.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

const STORAGE_KEY_AUDIO = 'gh-projects-bgm-state';

interface BackgroundAudioState {
  silenced: boolean;
  activePlayback: boolean;
}

export function useMusicPlayer() {
  const playerElementRef = useRef<HTMLAudioElement | null>(null);
  
  const loadSavedPreference = useCallback(() => {
    try {
      const savedState = localStorage.getItem(STORAGE_KEY_AUDIO);
      return savedState === 'silent';
    } catch {
      return false;
    }
  }, []);

  const [audioState, setAudioState] = useState<BackgroundAudioState>(() => ({
    silenced: loadSavedPreference(),
    activePlayback: false,
  }));

  const persistPreference = useCallback((silenceMode: boolean) => {
    try {
      localStorage.setItem(STORAGE_KEY_AUDIO, silenceMode ? 'silent' : 'audible');
    } catch {
      // Silent fail if localStorage unavailable
    }
  }, []);

  const handleToggleSound = useCallback(() => {
    setAudioState((current) => {
      const newSilenceState = !current.silenced;
      persistPreference(newSilenceState);
      return { ...current, silenced: newSilenceState };
    });
  }, [persistPreference]);

  const attachAudioElement = useCallback((element: HTMLAudioElement | null) => {
    playerElementRef.current = element;
    
    if (element) {
      const onPlaybackStart = () => {
        setAudioState((prev) => ({ ...prev, activePlayback: true }));
      };
      const onPlaybackStop = () => {
        setAudioState((prev) => ({ ...prev, activePlayback: false }));
      };

      element.addEventListener('playing', onPlaybackStart);
      element.addEventListener('pause', onPlaybackStop);
      element.addEventListener('ended', onPlaybackStop);
      
      return () => {
        element.removeEventListener('playing', onPlaybackStart);
        element.removeEventListener('pause', onPlaybackStop);
        element.removeEventListener('ended', onPlaybackStop);
      };
    }
  }, []);

  useEffect(() => {
    const handleTabVisibility = () => {
      const playerEl = playerElementRef.current;
      if (!playerEl) return;

      if (document.hidden) {
        playerEl.pause();
      } else if (!audioState.silenced) {
        playerEl.play().catch(() => {
          // Browser might block autoplay
        });
      }
    };

    document.addEventListener('visibilitychange', handleTabVisibility);
    return () => document.removeEventListener('visibilitychange', handleTabVisibility);
  }, [audioState.silenced]);

  return {
    soundSilenced: audioState.silenced,
    playbackActive: audioState.activePlayback,
    toggleSound: handleToggleSound,
    attachAudioElement,
  };
}

