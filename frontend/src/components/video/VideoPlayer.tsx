/**
 * VideoPlayer — accessible HTML5 video player with standard playback controls.
 *
 * Features:
 * - Play/pause, seek bar, volume/mute, playback speed
 * - Fullscreen and picture-in-picture support
 * - Keyboard navigation and ARIA labels
 * - Captions/subtitle track support
 * - Inline autoplay (muted) mode for feed contexts
 * - Responsive design across breakpoints
 * - Error state handling with actionable messages
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  PictureInPicture2,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface VideoTrack {
  src: string;
  srclang: string;
  label: string;
  kind: 'subtitles' | 'captions';
  default?: boolean;
}

export interface VideoPlayerProps {
  /** URL of the video to play */
  src: string;
  /** Optional poster/thumbnail image URL */
  poster?: string;
  /** Video title for accessibility */
  title?: string;
  /** Enable inline autoplay (muted) for feed contexts */
  autoPlay?: boolean;
  /** Subtitle/caption tracks */
  tracks?: VideoTrack[];
  /** Additional CSS classes for the container */
  className?: string;
  /** Callback when video ends */
  onEnded?: () => void;
  /** Callback on playback error */
  onError?: (message: string) => void;
}

const PLAYBACK_SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function VideoPlayer({
  src,
  poster,
  title,
  autoPlay = false,
  tracks = [],
  className,
  onEnded,
  onError,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(autoPlay);
  const [volume, setVolume] = useState(autoPlay ? 0 : 1);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showControls, setShowControls] = useState(true);
  const hideControlsTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-hide controls after 3 seconds of inactivity
  const resetHideTimer = useCallback(() => {
    setShowControls(true);
    if (hideControlsTimer.current) clearTimeout(hideControlsTimer.current);
    hideControlsTimer.current = setTimeout(() => {
      if (isPlaying) setShowControls(false);
    }, 3000);
  }, [isPlaying]);

  useEffect(() => {
    return () => {
      if (hideControlsTimer.current) clearTimeout(hideControlsTimer.current);
    };
  }, []);

  // Video event handlers
  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (video) setCurrentTime(video.currentTime);
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    const video = videoRef.current;
    if (video) setDuration(video.duration);
  }, []);

  const handlePlay = useCallback(() => setIsPlaying(true), []);
  const handlePause = useCallback(() => setIsPlaying(false), []);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    onEnded?.();
  }, [onEnded]);

  const handleError = useCallback(() => {
    const video = videoRef.current;
    let message = 'An error occurred during playback.';
    if (video?.error) {
      switch (video.error.code) {
        case MediaError.MEDIA_ERR_ABORTED:
          message = 'Playback was aborted. Please try again.';
          break;
        case MediaError.MEDIA_ERR_NETWORK:
          message = 'A network error occurred. Check your connection and try again.';
          break;
        case MediaError.MEDIA_ERR_DECODE:
          message = 'This video format is not supported by your browser. Try a different format.';
          break;
        case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
          message =
            'This video format is not supported. Please upload an MP4, WebM, or MOV file.';
          break;
      }
    }
    setError(message);
    onError?.(message);
  }, [onError]);

  // Control actions
  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      // If autoplay muted, unmute on first user interaction
      if (autoPlay && video.muted) {
        video.muted = false;
        setIsMuted(false);
        setVolume(1);
      }
      video.play().catch(() => {
        /* handled by error event */
      });
    } else {
      video.pause();
    }
  }, [autoPlay]);

  const toggleMute = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !video.muted;
    setIsMuted(video.muted);
    if (!video.muted && volume === 0) {
      video.volume = 0.5;
      setVolume(0.5);
    }
  }, [volume]);

  const handleVolumeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;
    const val = parseFloat(e.target.value);
    video.volume = val;
    setVolume(val);
    video.muted = val === 0;
    setIsMuted(val === 0);
  }, []);

  const handleSeek = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const video = videoRef.current;
      const bar = progressRef.current;
      if (!video || !bar || !duration) return;
      const rect = bar.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      video.currentTime = ratio * duration;
    },
    [duration]
  );

  const toggleFullscreen = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    } else {
      container.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    }
  }, []);

  const togglePiP = useCallback(async () => {
    const video = videoRef.current;
    if (!video) return;
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
      } else {
        await video.requestPictureInPicture();
      }
    } catch {
      // PiP not supported — silently ignore
    }
  }, []);

  const changeSpeed = useCallback((speed: number) => {
    const video = videoRef.current;
    if (video) video.playbackRate = speed;
    setPlaybackSpeed(speed);
    setShowSpeedMenu(false);
  }, []);

  const retryPlayback = useCallback(() => {
    const video = videoRef.current;
    if (video) {
      setError(null);
      video.load();
    }
  }, []);

  // Keyboard controls
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const video = videoRef.current;
      if (!video) return;

      switch (e.key) {
        case ' ':
        case 'k':
          e.preventDefault();
          togglePlay();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          video.currentTime = Math.max(0, video.currentTime - 5);
          break;
        case 'ArrowRight':
          e.preventDefault();
          video.currentTime = Math.min(duration, video.currentTime + 5);
          break;
        case 'ArrowUp':
          e.preventDefault();
          video.volume = Math.min(1, video.volume + 0.1);
          setVolume(video.volume);
          break;
        case 'ArrowDown':
          e.preventDefault();
          video.volume = Math.max(0, video.volume - 0.1);
          setVolume(video.volume);
          break;
        case 'f':
          e.preventDefault();
          toggleFullscreen();
          break;
        case 'm':
          e.preventDefault();
          toggleMute();
          break;
      }
    },
    [togglePlay, toggleFullscreen, toggleMute, duration]
  );

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFsChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  if (error) {
    return (
      <div
        className={cn(
          'relative flex flex-col items-center justify-center gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-6',
          className
        )}
        role="alert"
      >
        <AlertTriangle className="h-8 w-8 text-destructive" />
        <p className="text-sm text-destructive text-center">{error}</p>
        <button
          type="button"
          onClick={retryPlayback}
          className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          aria-label="Retry playback"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn('group relative overflow-hidden rounded-lg bg-black', className)}
      onMouseMove={resetHideTimer}
      onMouseLeave={() => isPlaying && setShowControls(false)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="application"
      aria-label={title ? `Video player: ${title}` : 'Video player'}
    >
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        autoPlay={autoPlay}
        muted={autoPlay}
        playsInline
        className="h-full w-full cursor-pointer"
        onClick={togglePlay}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={handlePlay}
        onPause={handlePause}
        onEnded={handleEnded}
        onError={handleError}
        aria-label={title || 'Video content'}
      >
        {tracks.map((track) => (
          <track
            key={`${track.srclang}-${track.kind}`}
            src={track.src}
            kind={track.kind}
            srcLang={track.srclang}
            label={track.label}
            default={track.default}
          />
        ))}
      </video>

      {/* Controls overlay */}
      <div
        className={cn(
          'absolute inset-x-0 bottom-0 flex flex-col gap-1 bg-gradient-to-t from-black/80 to-transparent p-2 transition-opacity duration-300',
          showControls || !isPlaying ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        aria-hidden={!showControls && isPlaying}
      >
        {/* Seek bar */}
        <div
          ref={progressRef}
          className="group/seek relative h-1.5 w-full cursor-pointer rounded-full bg-white/30 hover:h-2.5 transition-all"
          onClick={handleSeek}
          role="slider"
          aria-label="Seek"
          aria-valuemin={0}
          aria-valuemax={Math.round(duration)}
          aria-valuenow={Math.round(currentTime)}
          aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
          tabIndex={0}
        >
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-primary"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Controls row */}
        <div className="flex items-center gap-2 text-white">
          {/* Play/Pause */}
          <button
            type="button"
            onClick={togglePlay}
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-white/20 transition-colors"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>

          {/* Volume */}
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={toggleMute}
              className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-white/20 transition-colors"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="h-4 w-4" />
              ) : (
                <Volume2 className="h-4 w-4" />
              )}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="hidden w-16 cursor-pointer sm:block"
              aria-label="Volume"
            />
          </div>

          {/* Time */}
          <span className="text-xs tabular-nums" aria-live="off">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          <div className="flex-1" />

          {/* Speed */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowSpeedMenu((v) => !v)}
              className="flex h-8 items-center justify-center rounded-full px-2 text-xs font-medium hover:bg-white/20 transition-colors"
              aria-label={`Playback speed: ${playbackSpeed}x`}
              aria-expanded={showSpeedMenu}
              aria-haspopup="listbox"
            >
              {playbackSpeed}x
            </button>
            {showSpeedMenu && (
              <div
                className="absolute bottom-full right-0 mb-1 rounded-md bg-black/90 py-1 shadow-lg"
                role="listbox"
                aria-label="Playback speed options"
              >
                {PLAYBACK_SPEEDS.map((speed) => (
                  <button
                    key={speed}
                    type="button"
                    onClick={() => changeSpeed(speed)}
                    className={cn(
                      'block w-full px-4 py-1 text-left text-xs hover:bg-white/20 transition-colors',
                      speed === playbackSpeed && 'text-primary font-semibold'
                    )}
                    role="option"
                    aria-selected={speed === playbackSpeed}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* PiP */}
          {'pictureInPictureEnabled' in document && (
            <button
              type="button"
              onClick={togglePiP}
              className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-white/20 transition-colors"
              aria-label="Picture-in-picture"
            >
              <PictureInPicture2 className="h-4 w-4" />
            </button>
          )}

          {/* Fullscreen */}
          <button
            type="button"
            onClick={toggleFullscreen}
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-white/20 transition-colors"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <Minimize className="h-4 w-4" />
            ) : (
              <Maximize className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Big play button overlay when paused */}
      {!isPlaying && !autoPlay && (
        <button
          type="button"
          onClick={togglePlay}
          className="absolute inset-0 flex items-center justify-center bg-black/20 transition-opacity"
          aria-label="Play video"
        >
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/90 text-primary-foreground shadow-lg">
            <Play className="h-8 w-8" />
          </div>
        </button>
      )}
    </div>
  );
}
