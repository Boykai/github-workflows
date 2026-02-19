/**
 * Unit tests for RateLimitIndicator component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RateLimitIndicator } from './RateLimitIndicator';

describe('RateLimitIndicator', () => {
  it('renders null when remaining is null', () => {
    const { container } = render(<RateLimitIndicator remaining={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('shows remaining count with total', () => {
    render(<RateLimitIndicator remaining={3000} total={4000} />);
    expect(screen.getByText('3,000 / 4,000 API calls remaining')).toBeDefined();
  });

  it('uses default total of 4000', () => {
    render(<RateLimitIndicator remaining={2000} />);
    expect(screen.getByText('2,000 / 4,000 API calls remaining')).toBeDefined();
  });

  it('shows warning when critical (< 5%)', () => {
    render(<RateLimitIndicator remaining={100} total={4000} />);
    expect(screen.getByText(/Rate limit nearly exhausted/)).toBeDefined();
  });

  it('applies low class when < 20%', () => {
    const { container } = render(<RateLimitIndicator remaining={600} total={4000} />);
    const indicator = container.querySelector('.rate-limit-indicator');
    expect(indicator?.className).toContain('low');
  });

  it('applies critical class when < 5%', () => {
    const { container } = render(<RateLimitIndicator remaining={100} total={4000} />);
    const indicator = container.querySelector('.rate-limit-indicator');
    expect(indicator?.className).toContain('critical');
  });

  it('does not apply low or critical class when above 20%', () => {
    const { container } = render(<RateLimitIndicator remaining={3000} total={4000} />);
    const indicator = container.querySelector('.rate-limit-indicator');
    expect(indicator?.className).not.toContain('low');
    expect(indicator?.className).not.toContain('critical');
  });
});
