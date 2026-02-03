/**
 * RainbowIndicator Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RainbowIndicator } from './RainbowIndicator';

describe('RainbowIndicator', () => {
  it('should not render when show is false', () => {
    const { container } = render(<RainbowIndicator show={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render when show is true', () => {
    render(<RainbowIndicator show={true} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/Success!/)).toBeInTheDocument();
  });

  it('should have accessible attributes', () => {
    render(<RainbowIndicator show={true} />);
    const indicator = screen.getByRole('status');
    
    expect(indicator).toHaveAttribute('aria-live', 'polite');
    expect(indicator).toHaveAttribute('aria-label', expect.stringContaining('Success'));
    
    const graphic = screen.getByRole('img');
    expect(graphic).toHaveAttribute('aria-label', expect.stringContaining('Rainbow'));
  });

  it('should have a dismiss button with accessible label', () => {
    render(<RainbowIndicator show={true} />);
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    expect(dismissButton).toBeInTheDocument();
  });

  it('should call onDismiss when dismiss button is clicked', () => {
    vi.useFakeTimers();
    const onDismiss = vi.fn();
    
    render(<RainbowIndicator show={true} onDismiss={onDismiss} />);
    
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);
    
    // Fast-forward through fade animation
    vi.advanceTimersByTime(1000);
    
    expect(onDismiss).toHaveBeenCalledTimes(1);
    vi.restoreAllMocks();
  });

  it('should render rainbow SVG with multiple colored arcs', () => {
    render(<RainbowIndicator show={true} />);
    
    const svg = screen.getByRole('img');
    expect(svg).toBeInTheDocument();
    
    // Check that SVG has rainbow arcs (paths)
    const paths = svg.querySelectorAll('path');
    expect(paths.length).toBeGreaterThan(0);
    
    // Verify different colors are used
    const colors = Array.from(paths).map(path => path.getAttribute('stroke'));
    const uniqueColors = new Set(colors);
    expect(uniqueColors.size).toBeGreaterThan(1);
  });

  it('should render celebration emoji', () => {
    render(<RainbowIndicator show={true} />);
    expect(screen.getByText(/🎉/)).toBeInTheDocument();
  });
});
