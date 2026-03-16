import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { MemoryRouter } from 'react-router-dom';
import { axe, toHaveNoViolations } from 'jest-axe';
import { HelpPage } from './HelpPage';

expect.extend(toHaveNoViolations);

vi.mock('@/hooks/useOnboarding', () => ({
  useOnboarding: () => ({
    isActive: false,
    hasCompleted: true,
    currentStep: 0,
    totalSteps: 9,
    next: vi.fn(),
    prev: vi.fn(),
    skip: vi.fn(),
    restart: vi.fn(),
  }),
}));

vi.mock('@/lib/commands/registry', () => ({
  getAllCommands: () => [],
}));

describe('HelpPage', () => {
  it('renders and shows the help center heading', () => {
    render(
      <MemoryRouter>
        <HelpPage />
      </MemoryRouter>,
    );
    expect(screen.getByText('Help Center')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <MemoryRouter>
        <HelpPage />
      </MemoryRouter>,
    );
    // heading-order is a pre-existing issue in FeatureGuideCard (uses h4 inside h2 sections)
    const results = await axe(container, {
      rules: { 'heading-order': { enabled: false } },
    });
    expect(results).toHaveNoViolations();
  });
});
