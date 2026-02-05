/**
 * Elevator music background player component.
 */

import { useEffect, useRef } from 'react';
import { useMusicPlayer } from '@/hooks/useMusicPlayer';
import './MusicPlayer.css';

export function MusicPlayer() {
  const { soundSilenced, playbackActive, toggleSound, attachAudioElement } = useMusicPlayer();
  const playerRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audioElement = playerRef.current;
    if (!audioElement) return;

    const cleanup = attachAudioElement(audioElement);
    
    // Control playback based on silenced state
    if (soundSilenced) {
      audioElement.pause();
    } else {
      audioElement.play().catch(() => {
        // Silently handle autoplay restrictions
      });
    }

    return cleanup;
  }, [attachAudioElement, soundSilenced]);

  const buttonLabel = soundSilenced ? 'Enable Background Music' : 'Disable Background Music';
  const statusIcon = soundSilenced ? '🔇' : (playbackActive ? '🎵' : '🔊');

  return (
    <div className="bgm-controller">
      <audio
        ref={playerRef}
        loop
        src="/elevator-music.wav"
        preload="auto"
      />
      <button
        onClick={toggleSound}
        className="bgm-toggle-btn"
        aria-label={buttonLabel}
        title={buttonLabel}
        type="button"
      >
        <span className="bgm-icon" aria-hidden="true">
          {statusIcon}
        </span>
      </button>
    </div>
  );
}
