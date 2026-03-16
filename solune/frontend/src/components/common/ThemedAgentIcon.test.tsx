import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ThemedAgentIcon, getThemedAgentVariant } from './ThemedAgentIcon';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('ThemedAgentIcon', () => {
  it('maps known agent slugs to explicit celestial variants', () => {
    expect(getThemedAgentVariant('copilot')).toBe('eclipse');
    expect(getThemedAgentVariant('copilot-review')).toBe('moon-phase');
    expect(getThemedAgentVariant('speckit.plan')).toBe('crescent');
    expect(getThemedAgentVariant('speckit.tasks')).toBe('constellation');
  });

  it('renders a themed icon when no avatar image is provided', () => {
    const { container } = render(<ThemedAgentIcon slug="copilot" name="GitHub Copilot" />);

    expect(container.querySelector('[data-agent-icon="eclipse"]')).toBeTruthy();
    expect(container.querySelector('svg')).toBeTruthy();
  });

  it('prefers avatar images and falls back to the celestial icon on load failure', () => {
    const { container } = render(
      <ThemedAgentIcon
        slug="copilot-review"
        name="Copilot Review"
        avatarUrl="https://example.com/avatar.png"
      />
    );

    const image = screen.getByAltText('Copilot Review');
    expect(image).toBeTruthy();

    fireEvent.error(image);

    expect(screen.queryByAltText('Copilot Review')).toBeNull();
    expect(container.querySelector('[data-agent-icon="moon-phase"]')).toBeTruthy();
    expect(container.querySelector('svg')).toBeTruthy();
  });

  it('honors an explicit icon name override', () => {
    const { container } = render(
      <ThemedAgentIcon slug="copilot" iconName="aurora" name="GitHub Copilot" />
    );

    expect(container.querySelector('[data-agent-icon="aurora"]')).toBeTruthy();
  });

  it('falls back to the initial when no slug is available', () => {
    render(<ThemedAgentIcon name="Agent Smith" />);

    expect(screen.getByText('A')).toBeTruthy();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<ThemedAgentIcon slug="copilot" name="GitHub Copilot" />);
    await expectNoA11yViolations(container);
  });
});
