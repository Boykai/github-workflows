/**
 * Hook for managing theme music playback with fade in/out effects.
 * Persists volume and mute preferences in localStorage.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const STORAGE_KEY_VOLUME = 'theme-music-volume';
const STORAGE_KEY_MUTED = 'theme-music-muted';
const DEFAULT_VOLUME = 0.3; // 30% volume
const FADE_DURATION_MS = 2000; // 2 seconds fade

interface UseThemeMusicReturn {
  isPlaying: boolean;
  isMuted: boolean;
  volume: number;
  isLoading: boolean;
  hasError: boolean;
  play: () => void;
  pause: () => void;
  togglePlayPause: () => void;
  toggleMute: () => void;
  setVolume: (volume: number) => void;
}

export function useThemeMusic(): UseThemeMusicReturn {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fadeIntervalRef = useRef<number | null>(null);
  
  // Load preferences from localStorage
  const [volume, setVolumeState] = useState<number>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_VOLUME);
    return saved ? parseFloat(saved) : DEFAULT_VOLUME;
  });
  
  const [isMuted, setIsMutedState] = useState<boolean>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_MUTED);
    return saved === 'true';
  });
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  // Initialize audio element
  useEffect(() => {
    const audio = new Audio('/theme-music.mp3');
    audio.loop = true;
    audio.volume = 0; // Start at 0 for fade in
    audioRef.current = audio;

    // Event listeners
    const handleCanPlay = () => {
      setIsLoading(false);
      setHasError(false);
    };

    const handleError = () => {
      setIsLoading(false);
      setHasError(true);
      console.warn('Theme music file not found or failed to load. Music playback disabled.');
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('error', handleError);
    audio.addEventListener('ended', handleEnded);

    // Cleanup
    return () => {
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('ended', handleEnded);
      
      if (fadeIntervalRef.current) {
        clearInterval(fadeIntervalRef.current);
      }
      
      audio.pause();
      audio.src = '';
    };
  }, []);

  // Apply mute state to audio element
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.muted = isMuted;
    }
  }, [isMuted]);

  // Fade in function
  const fadeIn = useCallback((targetVolume: number) => {
    if (!audioRef.current || fadeIntervalRef.current) return;

    const audio = audioRef.current;
    const startVolume = 0;
    const steps = 50;
    const stepDuration = FADE_DURATION_MS / steps;
    const volumeIncrement = (targetVolume - startVolume) / steps;
    let currentStep = 0;

    audio.volume = startVolume;

    fadeIntervalRef.current = window.setInterval(() => {
      currentStep++;
      if (currentStep >= steps || !audioRef.current) {
        if (audioRef.current) {
          audioRef.current.volume = targetVolume;
        }
        if (fadeIntervalRef.current) {
          clearInterval(fadeIntervalRef.current);
          fadeIntervalRef.current = null;
        }
      } else {
        audio.volume = startVolume + (volumeIncrement * currentStep);
      }
    }, stepDuration);
  }, []);

  // Fade out function
  const fadeOut = useCallback(() => {
    if (!audioRef.current || fadeIntervalRef.current) return;

    const audio = audioRef.current;
    const startVolume = audio.volume;
    const steps = 50;
    const stepDuration = FADE_DURATION_MS / steps;
    const volumeDecrement = startVolume / steps;
    let currentStep = 0;

    fadeIntervalRef.current = window.setInterval(() => {
      currentStep++;
      if (currentStep >= steps || !audioRef.current) {
        if (audioRef.current) {
          audioRef.current.volume = 0;
          audioRef.current.pause();
        }
        if (fadeIntervalRef.current) {
          clearInterval(fadeIntervalRef.current);
          fadeIntervalRef.current = null;
        }
        setIsPlaying(false);
      } else {
        audio.volume = startVolume - (volumeDecrement * currentStep);
      }
    }, stepDuration);
  }, []);

  // Play function
  const play = useCallback(() => {
    if (!audioRef.current || hasError || isPlaying) return;

    setIsLoading(true);
    audioRef.current.play()
      .then(() => {
        setIsPlaying(true);
        setIsLoading(false);
        fadeIn(volume);
      })
      .catch((error) => {
        console.error('Failed to play theme music:', error);
        setIsLoading(false);
        setHasError(true);
      });
  }, [hasError, isPlaying, volume, fadeIn]);

  // Pause function
  const pause = useCallback(() => {
    if (!audioRef.current || !isPlaying) return;

    // Clear any existing fade
    if (fadeIntervalRef.current) {
      clearInterval(fadeIntervalRef.current);
      fadeIntervalRef.current = null;
    }

    fadeOut();
  }, [isPlaying, fadeOut]);

  // Toggle play/pause
  const togglePlayPause = useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    const newMuted = !isMuted;
    setIsMutedState(newMuted);
    localStorage.setItem(STORAGE_KEY_MUTED, String(newMuted));
  }, [isMuted]);

  // Set volume
  const setVolume = useCallback((newVolume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, newVolume));
    setVolumeState(clampedVolume);
    localStorage.setItem(STORAGE_KEY_VOLUME, String(clampedVolume));
    
    // Update audio volume if playing and not fading
    if (audioRef.current && isPlaying && !fadeIntervalRef.current) {
      audioRef.current.volume = clampedVolume;
    }
  }, [isPlaying]);

  // Auto-play on mount (after a short delay to respect browser policies)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!hasError && !isMuted) {
        play();
      }
    }, 500);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  return {
    isPlaying,
    isMuted,
    volume,
    isLoading,
    hasError,
    play,
    pause,
    togglePlayPause,
    toggleMute,
    setVolume,
  };
}
