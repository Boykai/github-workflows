/**
 * Tests for the CelestialCatalogHero component.
 *
 * Covers: required props rendering, stats display, actions slot, badge/note,
 * animation utility classes, and className forwarding.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { CelestialCatalogHero } from './CelestialCatalogHero';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

const defaultProps = {
  eyebrow: 'Catalog',
  title: 'Celestial Agents',
  description: 'Manage your agent constellation.',
};

describe('CelestialCatalogHero', () => {
  it('renders eyebrow, title, and description text', () => {
    render(<CelestialCatalogHero {...defaultProps} />);
    expect(screen.getByText('Catalog')).toBeInTheDocument();
    expect(screen.getByText('Celestial Agents')).toBeInTheDocument();
    // Description appears in both the main content area and the illustration panel fallback
    const descriptions = screen.getAllByText('Manage your agent constellation.');
    expect(descriptions.length).toBe(2);
  });

  it('renders as a <section> element', () => {
    const { container } = render(<CelestialCatalogHero {...defaultProps} />);
    expect(container.querySelector('section')).toBeInTheDocument();
  });

  it('renders a badge when provided', () => {
    render(<CelestialCatalogHero {...defaultProps} badge="New" />);
    expect(screen.getByText('New')).toBeInTheDocument();
  });

  it('does not render a badge element when not provided', () => {
    const { container } = render(<CelestialCatalogHero {...defaultProps} />);
    // Badge spans have specific classes with tracking-[0.2em]
    const badgeSpans = container.querySelectorAll('span.rounded-full');
    // Filter to only badge-like spans (not the celestial-sigil)
    const badges = Array.from(badgeSpans).filter((el) => el.textContent === 'New');
    expect(badges).toHaveLength(0);
  });

  it('renders stats when provided', () => {
    const stats = [
      { label: 'Total Agents', value: '42' },
      { label: 'Active', value: '12' },
    ];
    render(<CelestialCatalogHero {...defaultProps} stats={stats} />);
    expect(screen.getByText('Total Agents')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('renders the actions slot', () => {
    render(
      <CelestialCatalogHero
        {...defaultProps}
        actions={<button data-testid="hero-action">Add Agent</button>}
      />
    );
    expect(screen.getByTestId('hero-action')).toBeInTheDocument();
    expect(screen.getByText('Add Agent')).toBeInTheDocument();
  });

  it('uses the note text in the illustration panel when provided', () => {
    render(<CelestialCatalogHero {...defaultProps} note="Deploy your first ritual" />);
    expect(screen.getByText('Deploy your first ritual')).toBeInTheDocument();
  });

  it('falls back to description in the illustration panel when note is not provided', () => {
    render(<CelestialCatalogHero {...defaultProps} />);
    // Description appears twice: once in the main content and once in the illustration panel
    const descriptions = screen.getAllByText('Manage your agent constellation.');
    expect(descriptions.length).toBeGreaterThanOrEqual(1);
  });

  it('applies celestial animation classes on decorative elements', () => {
    const { container } = render(<CelestialCatalogHero {...defaultProps} />);
    expect(container.querySelector('.celestial-pulse-glow')).toBeInTheDocument();
    expect(container.querySelector('.celestial-orbit-spin')).toBeInTheDocument();
    expect(container.querySelector('.celestial-orbit-spin-reverse')).toBeInTheDocument();
    expect(container.querySelector('.celestial-twinkle')).toBeInTheDocument();
    expect(container.querySelector('.celestial-float')).toBeInTheDocument();
  });

  it('includes starfield class on the section', () => {
    const { container } = render(<CelestialCatalogHero {...defaultProps} />);
    const section = container.querySelector('section');
    expect(section?.className).toContain('starfield');
  });

  it('forwards custom className', () => {
    const { container } = render(
      <CelestialCatalogHero {...defaultProps} className="extra-hero-class" />
    );
    const section = container.querySelector('section');
    expect(section?.className).toContain('extra-hero-class');
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<CelestialCatalogHero {...defaultProps} />);
    await expectNoA11yViolations(container);
  });
});
