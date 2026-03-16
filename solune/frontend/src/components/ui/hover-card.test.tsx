import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { HoverCard, HoverCardTrigger, HoverCardContent } from './hover-card';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('HoverCard', () => {
  it('renders without crashing', () => {
    render(
      <HoverCard>
        <HoverCardTrigger asChild>
          <button type="button">Hover trigger</button>
        </HoverCardTrigger>
        <HoverCardContent>
          <p>Preview content</p>
        </HoverCardContent>
      </HoverCard>
    );

    expect(screen.getByRole('button', { name: 'Hover trigger' })).toBeInTheDocument();
  });

  it('shows content on hover trigger', async () => {
    const user = userEvent.setup();

    render(
      <HoverCard openDelay={0} closeDelay={0}>
        <HoverCardTrigger asChild>
          <button type="button">Agent name</button>
        </HoverCardTrigger>
        <HoverCardContent>
          <p>Agent description and tools preview</p>
        </HoverCardContent>
      </HoverCard>
    );

    await user.hover(screen.getByRole('button', { name: 'Agent name' }));

    expect(await screen.findByText('Agent description and tools preview')).toBeInTheDocument();
  });

  it('applies custom className to content', async () => {
    const user = userEvent.setup();

    render(
      <HoverCard openDelay={0} closeDelay={0}>
        <HoverCardTrigger asChild>
          <button type="button">Trigger</button>
        </HoverCardTrigger>
        <HoverCardContent className="custom-class" data-testid="hc-content">
          <p>Content</p>
        </HoverCardContent>
      </HoverCard>
    );

    await user.hover(screen.getByRole('button', { name: 'Trigger' }));
    const content = await screen.findByTestId('hc-content');
    expect(content.className).toContain('custom-class');
  });

  it('respects side prop', async () => {
    const user = userEvent.setup();

    render(
      <HoverCard openDelay={0} closeDelay={0}>
        <HoverCardTrigger asChild>
          <button type="button">Trigger</button>
        </HoverCardTrigger>
        <HoverCardContent side="right" data-testid="hc-content">
          <p>Side content</p>
        </HoverCardContent>
      </HoverCard>
    );

    await user.hover(screen.getByRole('button', { name: 'Trigger' }));
    const content = await screen.findByTestId('hc-content');
    expect(content).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <HoverCard>
        <HoverCardTrigger asChild>
          <button type="button">Hover trigger</button>
        </HoverCardTrigger>
        <HoverCardContent>
          <p>Preview content</p>
        </HoverCardContent>
      </HoverCard>
    );
    await expectNoA11yViolations(container);
  });
});
