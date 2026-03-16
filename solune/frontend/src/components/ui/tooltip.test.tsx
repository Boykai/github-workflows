import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { Tooltip } from './tooltip';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('Tooltip', () => {
  it('renders registry-backed tooltip content on hover', async () => {
    const user = userEvent.setup();

    render(
      <Tooltip contentKey="agents.panel.bulkUpdateButton">
        <button type="button">Update all models</button>
      </Tooltip>
    );

    await user.hover(screen.getByRole('button', { name: 'Update all models' }));

    const tooltip = await screen.findByRole('tooltip');
    expect(tooltip).toBeInTheDocument();
    expect(within(tooltip).getByText('Bulk Model Update')).toBeInTheDocument();
    expect(
      within(tooltip).getByText(/Change the default AI model for multiple agents at once/i)
    ).toBeInTheDocument();
  });

  it('renders direct content with optional metadata', async () => {
    const user = userEvent.setup();

    render(
      <Tooltip
        content="Immediate explanation for a dynamic action."
        title="Dynamic tooltip"
        learnMoreUrl="https://example.test/docs"
      >
        <button type="button">Dynamic action</button>
      </Tooltip>
    );

    await user.hover(screen.getByRole('button', { name: 'Dynamic action' }));

    const tooltip = await screen.findByRole('tooltip');
    expect(tooltip).toBeInTheDocument();
    expect(within(tooltip).getByText('Dynamic tooltip')).toBeInTheDocument();
    expect(
      within(tooltip).getByText('Immediate explanation for a dynamic action.')
    ).toBeInTheDocument();
    expect(within(tooltip).getByRole('link', { name: 'Learn more →' })).toHaveAttribute(
      'href',
      'https://example.test/docs'
    );
  });

  it('gracefully skips tooltip rendering when the key is missing', async () => {
    const user = userEvent.setup();

    render(
      <Tooltip contentKey="missing.registry.entry">
        <button type="button">Missing tooltip</button>
      </Tooltip>
    );

    await user.hover(screen.getByRole('button', { name: 'Missing tooltip' }));

    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <Tooltip contentKey="agents.panel.bulkUpdateButton">
        <button type="button">Update all models</button>
      </Tooltip>
    );
    await expectNoA11yViolations(container);
  });
});
