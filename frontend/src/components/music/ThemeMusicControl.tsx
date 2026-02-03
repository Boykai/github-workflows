/**
 * Theme music control component.
 * Displays a music control icon in the header with play/pause/mute controls and volume slider.
 */

import { useState, useRef, useEffect } from 'react';
import './ThemeMusicControl.css';

interface ThemeMusicControlProps {
  isPlaying: boolean;
  isMuted: boolean;
  volume: number;
  isLoading: boolean;
  hasError: boolean;
  onTogglePlayPause: () => void;
  onToggleMute: () => void;
  onVolumeChange: (volume: number) => void;
}

export function ThemeMusicControl({
  isPlaying,
  isMuted,
  volume,
  isLoading,
  hasError,
  onTogglePlayPause,
  onToggleMute,
  onVolumeChange,
}: ThemeMusicControlProps) {
  const [isOpen, setIsOpen] = useState(false);
  const controlRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (controlRef.current && !controlRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Don't render if there's an error (music file not found)
  if (hasError) {
    return null;
  }

  const volumePercentage = Math.round(volume * 100);
  const effectiveVolume = isMuted ? 0 : volume;

  return (
    <div className="theme-music-control" ref={controlRef}>
      <button
        className="music-toggle-button"
        onClick={() => setIsOpen(!isOpen)}
        title={isPlaying ? 'Music playing' : 'Music paused'}
        aria-label="Theme music controls"
      >
        {isLoading ? (
          <span className="music-icon loading">⟳</span>
        ) : (
          <MusicIcon isPlaying={isPlaying} isMuted={isMuted} />
        )}
      </button>

      {isOpen && (
        <div className="music-control-panel">
          <div className="control-header">
            <span className="control-title">Theme Music</span>
          </div>

          <div className="control-section">
            <button
              className="control-button"
              onClick={onTogglePlayPause}
              disabled={isLoading}
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>

            <button
              className="control-button"
              onClick={onToggleMute}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? '🔇' : '🔊'}
            </button>
          </div>

          <div className="volume-control">
            <label className="volume-label">
              <span className="volume-icon">{getVolumeIcon(effectiveVolume)}</span>
              <input
                type="range"
                min="0"
                max="100"
                value={volumePercentage}
                onChange={(e) => onVolumeChange(Number(e.target.value) / 100)}
                className="volume-slider"
                title={`Volume: ${volumePercentage}%`}
              />
              <span className="volume-text">{volumePercentage}%</span>
            </label>
          </div>

          {isPlaying && (
            <div className="now-playing">
              <span className="now-playing-indicator">♪</span>
              <span className="now-playing-text">Now playing</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MusicIcon({ isPlaying, isMuted }: { isPlaying: boolean; isMuted: boolean }) {
  if (isMuted) {
    return <span className="music-icon muted">🔇</span>;
  }
  if (isPlaying) {
    return <span className="music-icon playing">🎵</span>;
  }
  return <span className="music-icon paused">🎵</span>;
}

function getVolumeIcon(volume: number): string {
  if (volume === 0) return '🔇';
  if (volume < 0.5) return '🔉';
  return '🔊';
}
