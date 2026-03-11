/**
 * Tests for the AppPage (homepage) component.
 *
 * Covers: hero image rendering, alt text accessibility, quick-link navigation
 * cards, and key content sections.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { MemoryRouter } from 'react-router-dom';
import { AppPage } from './AppPage';

function renderAppPage() {
  return render(
    <MemoryRouter>
      <AppPage />
    </MemoryRouter>
  );
}

describe('AppPage', () => {
  it('renders the hero heading', () => {
    renderAppPage();
    expect(screen.getByText('Change your project mindset.')).toBeInTheDocument();
  });

  it('renders the hero image with descriptive alt text', () => {
    renderAppPage();
    const img = screen.getByRole('img', { name: /solune/i });
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute(
      'alt',
      'Solune — a celestial illustration of the sun and moon orbiting together against a starry sky'
    );
  });

  it('renders the hero image with correct src path', () => {
    renderAppPage();
    const img = screen.getByRole('img', { name: /solune/i });
    expect(img).toHaveAttribute('src', '/images/hero-solune.svg');
  });

  it('renders the hero image with explicit width and height for layout stability', () => {
    renderAppPage();
    const img = screen.getByRole('img', { name: /solune/i });
    expect(img).toHaveAttribute('width', '800');
    expect(img).toHaveAttribute('height', '400');
  });

  it('renders the hero image with responsive CSS classes', () => {
    renderAppPage();
    const img = screen.getByRole('img', { name: /solune/i });
    expect(img.className).toContain('w-full');
    expect(img.className).toContain('max-w-lg');
  });

  it('renders all four quick-link cards', () => {
    renderAppPage();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Agents Pipelines')).toBeInTheDocument();
    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.getByText('Chores')).toBeInTheDocument();
  });

  it('renders the daily affirmation section', () => {
    renderAppPage();
    expect(screen.getByText('Daily affirmation')).toBeInTheDocument();
  });
});
