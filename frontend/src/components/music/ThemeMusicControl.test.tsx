/**
 * Tests for ThemeMusicControl component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeMusicControl } from './ThemeMusicControl';

describe('ThemeMusicControl', () => {
  const defaultProps = {
    isPlaying: false,
    isMuted: false,
    volume: 0.3,
    isLoading: false,
    hasError: false,
    onTogglePlayPause: vi.fn(),
    onToggleMute: vi.fn(),
    onVolumeChange: vi.fn(),
  };

  it('should not render when hasError is true', () => {
    const { container } = render(
      <ThemeMusicControl {...defaultProps} hasError={true} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render music toggle button', () => {
    render(<ThemeMusicControl {...defaultProps} />);
    const button = screen.getByLabelText('Theme music controls');
    expect(button).toBeTruthy();
  });

  it('should show loading icon when isLoading is true', () => {
    render(<ThemeMusicControl {...defaultProps} isLoading={true} />);
    const button = screen.getByLabelText('Theme music controls');
    expect(button.textContent).toContain('⟳');
  });

  it('should open control panel when toggle button is clicked', () => {
    render(<ThemeMusicControl {...defaultProps} />);
    const button = screen.getByLabelText('Theme music controls');
    
    fireEvent.click(button);
    
    expect(screen.getByText('Theme Music')).toBeTruthy();
  });

  it('should call onTogglePlayPause when play/pause button is clicked', () => {
    const onTogglePlayPause = vi.fn();
    render(
      <ThemeMusicControl {...defaultProps} onTogglePlayPause={onTogglePlayPause} />
    );
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    const playButton = screen.getByTitle('Play');
    fireEvent.click(playButton);
    
    expect(onTogglePlayPause).toHaveBeenCalledTimes(1);
  });

  it('should call onToggleMute when mute button is clicked', () => {
    const onToggleMute = vi.fn();
    render(
      <ThemeMusicControl {...defaultProps} onToggleMute={onToggleMute} />
    );
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    const muteButton = screen.getByTitle('Mute');
    fireEvent.click(muteButton);
    
    expect(onToggleMute).toHaveBeenCalledTimes(1);
  });

  it('should call onVolumeChange when volume slider is adjusted', () => {
    const onVolumeChange = vi.fn();
    render(
      <ThemeMusicControl {...defaultProps} onVolumeChange={onVolumeChange} />
    );
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    const slider = screen.getByTitle(/Volume:/);
    fireEvent.change(slider, { target: { value: '50' } });
    
    expect(onVolumeChange).toHaveBeenCalledWith(0.5);
  });

  it('should display "Now playing" indicator when isPlaying is true', () => {
    render(<ThemeMusicControl {...defaultProps} isPlaying={true} />);
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    expect(screen.getByText('Now playing')).toBeTruthy();
  });

  it('should not display "Now playing" indicator when isPlaying is false', () => {
    render(<ThemeMusicControl {...defaultProps} isPlaying={false} />);
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    expect(screen.queryByText('Now playing')).toBeNull();
  });

  it('should show correct volume percentage', () => {
    render(<ThemeMusicControl {...defaultProps} volume={0.75} />);
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    expect(screen.getByText('75%')).toBeTruthy();
  });

  it('should display pause button when playing', () => {
    render(<ThemeMusicControl {...defaultProps} isPlaying={true} />);
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    expect(screen.getByTitle('Pause')).toBeTruthy();
  });

  it('should display play button when paused', () => {
    render(<ThemeMusicControl {...defaultProps} isPlaying={false} />);
    
    const button = screen.getByLabelText('Theme music controls');
    fireEvent.click(button);
    
    expect(screen.getByTitle('Play')).toBeTruthy();
  });
});
