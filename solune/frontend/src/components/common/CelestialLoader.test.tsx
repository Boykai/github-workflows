/**
 * Tests for the CelestialLoader component.
 *
 * Covers: default rendering, size variants, custom label, accessibility,
 * animation classes, and className forwarding.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { CelestialLoader } from './CelestialLoader';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('CelestialLoader', () => {
  it('renders with role="status" for accessibility', () => {
    render(<CelestialLoader />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays the default "Loading…" label as sr-only text', () => {
    render(<CelestialLoader />);
    const label = screen.getByText('Loading…');
    expect(label).toBeInTheDocument();
    expect(label.className).toContain('sr-only');
  });

  it('accepts a custom label', () => {
    render(<CelestialLoader label="Fetching agents…" />);
    expect(screen.getByText('Fetching agents…')).toBeInTheDocument();
  });

  it('renders the medium size variant by default', () => {
    const { container } = render(<CelestialLoader />);
    const orbitWrapper = container.querySelector('.relative');
    expect(orbitWrapper?.className).toContain('h-12');
    expect(orbitWrapper?.className).toContain('w-12');
  });

  it('renders the small size variant', () => {
    const { container } = render(<CelestialLoader size="sm" />);
    const orbitWrapper = container.querySelector('.relative');
    expect(orbitWrapper?.className).toContain('h-8');
    expect(orbitWrapper?.className).toContain('w-8');
  });

  it('renders the large size variant', () => {
    const { container } = render(<CelestialLoader size="lg" />);
    const orbitWrapper = container.querySelector('.relative');
    expect(orbitWrapper?.className).toContain('h-16');
    expect(orbitWrapper?.className).toContain('w-16');
  });

  it('applies the celestial-pulse-glow animation to the central sun', () => {
    const { container } = render(<CelestialLoader />);
    const sun = container.querySelector('.bg-primary');
    expect(sun?.className).toContain('celestial-pulse-glow');
  });

  it('applies the celestial-orbit-spin-fast animation to the orbit ring', () => {
    const { container } = render(<CelestialLoader />);
    const orbitRing = container.querySelector('.celestial-orbit-spin-fast');
    expect(orbitRing).toBeInTheDocument();
    expect(orbitRing?.className).toContain('rounded-full');
    expect(orbitRing?.className).toContain('border');
  });

  it('contains the orbiting planet element', () => {
    const { container } = render(<CelestialLoader />);
    const planet = container.querySelector('.bg-gold');
    expect(planet).toBeInTheDocument();
  });

  it('forwards custom className to the root element', () => {
    const { container } = render(<CelestialLoader className="my-custom-class" />);
    const root = container.firstElementChild;
    expect(root?.className).toContain('my-custom-class');
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<CelestialLoader />);
    await expectNoA11yViolations(container);
  });
});
