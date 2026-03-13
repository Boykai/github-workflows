/**
 * Tests for VideoPlayer component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { VideoPlayer } from './VideoPlayer';

describe('VideoPlayer', () => {
  it('renders video element with src', () => {
    render(<VideoPlayer src="/test-video.mp4" />);
    const video = document.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video?.src).toContain('/test-video.mp4');
  });

  it('renders with title as aria-label', () => {
    render(<VideoPlayer src="/video.mp4" title="My Video" />);
    const container = screen.getByRole('application');
    expect(container).toHaveAttribute('aria-label', 'Video player: My Video');
  });

  it('renders play button when not playing', () => {
    render(<VideoPlayer src="/video.mp4" />);
    const playButton = screen.getByLabelText('Play video');
    expect(playButton).toBeInTheDocument();
  });

  it('renders playback controls', () => {
    render(<VideoPlayer src="/video.mp4" />);
    expect(screen.getByLabelText('Play')).toBeInTheDocument();
    expect(screen.getByLabelText('Mute')).toBeInTheDocument();
    expect(screen.getByLabelText('Enter fullscreen')).toBeInTheDocument();
  });

  it('renders seek bar with slider role', () => {
    render(<VideoPlayer src="/video.mp4" />);
    const slider = screen.getByRole('slider', { name: 'Seek' });
    expect(slider).toBeInTheDocument();
  });

  it('renders playback speed button', () => {
    render(<VideoPlayer src="/video.mp4" />);
    const speedButton = screen.getByLabelText(/Playback speed/);
    expect(speedButton).toBeInTheDocument();
    expect(speedButton).toHaveTextContent('1x');
  });

  it('shows speed menu when speed button is clicked', () => {
    render(<VideoPlayer src="/video.mp4" />);
    const speedButton = screen.getByLabelText(/Playback speed/);
    fireEvent.click(speedButton);
    expect(screen.getByRole('listbox', { name: 'Playback speed options' })).toBeInTheDocument();
  });

  it('renders volume slider', () => {
    render(<VideoPlayer src="/video.mp4" />);
    const volumeSlider = screen.getByLabelText('Volume');
    expect(volumeSlider).toBeInTheDocument();
  });

  it('renders subtitle tracks when provided', () => {
    render(
      <VideoPlayer
        src="/video.mp4"
        tracks={[{ src: '/subs.vtt', srclang: 'en', label: 'English', kind: 'subtitles' }]}
      />
    );
    const video = document.querySelector('video');
    const track = video?.querySelector('track');
    expect(track).toBeInTheDocument();
    expect(track?.getAttribute('srclang')).toBe('en');
  });

  it('sets autoplay and muted when autoPlay is true', () => {
    render(<VideoPlayer src="/video.mp4" autoPlay />);
    const video = document.querySelector('video');
    expect(video?.autoplay).toBe(true);
    expect(video?.muted).toBe(true);
  });

  it('renders error state with retry button when error occurs', () => {
    const onError = vi.fn();
    render(<VideoPlayer src="/video.mp4" onError={onError} />);
    const video = document.querySelector('video');

    // Simulate error
    fireEvent.error(video!);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByLabelText('Retry playback')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<VideoPlayer src="/video.mp4" className="custom-class" />);
    const container = screen.getByRole('application');
    expect(container.className).toContain('custom-class');
  });

  it('displays time as 0:00 / 0:00 initially', () => {
    render(<VideoPlayer src="/video.mp4" />);
    expect(screen.getByText('0:00 / 0:00')).toBeInTheDocument();
  });
});
