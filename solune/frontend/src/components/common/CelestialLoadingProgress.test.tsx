import { describe, expect, it, vi } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { CelestialLoadingProgress } from './CelestialLoadingProgress';

vi.mock('@/components/common/CelestialLoader', () => ({
  CelestialLoader: () => <div data-testid="celestial-loader" />,
}));

describe('CelestialLoadingProgress', () => {
  it('renders initial phase label with zero completions', () => {
    render(
      <CelestialLoadingProgress
        phases={[
          { label: 'Connecting to GitHub…', complete: false },
          { label: 'Loading project board…', complete: false },
        ]}
      />
    );

    expect(screen.getByText('Connecting to GitHub…')).toBeInTheDocument();
  });

  it('updates ring progress as phases complete', () => {
    render(
      <CelestialLoadingProgress
        phases={[
          { label: 'Connecting to GitHub…', complete: true },
          { label: 'Loading project board…', complete: true },
          { label: 'Loading pipelines…', complete: false },
          { label: 'Loading agents…', complete: false },
        ]}
      />
    );

    const progressbar = screen.getByRole('progressbar');
    // 2 of 4 phases complete = 50%
    expect(progressbar).toHaveAttribute('aria-valuenow', '50');
  });

  it('exposes role="progressbar" with correct aria-valuenow', () => {
    render(
      <CelestialLoadingProgress
        phases={[
          { label: 'Phase A', complete: true },
          { label: 'Phase B', complete: false },
        ]}
      />
    );

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '50');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('shows last phase label when all phases complete', () => {
    render(
      <CelestialLoadingProgress
        phases={[
          { label: 'Phase A', complete: true },
          { label: 'Phase B', complete: true },
        ]}
      />
    );

    expect(screen.getByText('Phase B')).toBeInTheDocument();
  });

  it('handles empty phases array gracefully', () => {
    render(<CelestialLoadingProgress phases={[]} />);

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '100');
  });

  // Accessibility tests (T008 + T009)
  it('has correct accessibility attributes on progressbar', () => {
    render(
      <CelestialLoadingProgress
        phases={[{ label: 'Loading…', complete: false }]}
      />
    );

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
    expect(progressbar).toHaveAttribute('aria-label', 'Loading progress');
  });

  it('marks twinkling star decorations with aria-hidden', () => {
    render(
      <CelestialLoadingProgress
        phases={[{ label: 'Loading…', complete: false }]}
      />
    );

    const stars = screen.getAllByText('✦');
    for (const star of stars) {
      expect(star).toHaveAttribute('aria-hidden', 'true');
    }
  });

  it('embeds CelestialLoader inside the ring', () => {
    render(
      <CelestialLoadingProgress
        phases={[{ label: 'Loading…', complete: false }]}
      />
    );

    expect(screen.getByTestId('celestial-loader')).toBeInTheDocument();
  });
});
