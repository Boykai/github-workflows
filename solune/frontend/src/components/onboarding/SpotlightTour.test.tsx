import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { SpotlightTour } from './SpotlightTour';

vi.mock('@/hooks/useOnboarding', () => ({
  useOnboarding: () => ({
    isActive: true,
    currentStep: 0,
    totalSteps: 9,
    next: vi.fn(),
    prev: vi.fn(),
    skip: vi.fn(),
  }),
}));

describe('SpotlightTour', () => {
  it('renders the first tour step', () => {
    render(
      <SpotlightTour isSidebarCollapsed={false} onToggleSidebar={vi.fn()} />,
    );
    expect(screen.getByText('Welcome to Solune')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <SpotlightTour isSidebarCollapsed={false} onToggleSidebar={vi.fn()} />,
    );
    await expectNoA11yViolations(container);
  });
});
