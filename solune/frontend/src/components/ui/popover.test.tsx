import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { Popover, PopoverTrigger, PopoverContent, PopoverClose } from './popover';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('Popover', () => {
  it('renders without crashing', () => {
    render(
      <Popover>
        <PopoverTrigger asChild>
          <button type="button">Open popover</button>
        </PopoverTrigger>
        <PopoverContent>
          <p>Popover body</p>
        </PopoverContent>
      </Popover>
    );

    expect(screen.getByRole('button', { name: 'Open popover' })).toBeInTheDocument();
  });

  it('shows content on click', async () => {
    const user = userEvent.setup();

    render(
      <Popover>
        <PopoverTrigger asChild>
          <button type="button">Open menu</button>
        </PopoverTrigger>
        <PopoverContent>
          <p>Menu content</p>
        </PopoverContent>
      </Popover>
    );

    await user.click(screen.getByRole('button', { name: 'Open menu' }));

    expect(await screen.findByText('Menu content')).toBeInTheDocument();
  });

  it('hides content on Escape', async () => {
    const user = userEvent.setup();

    render(
      <Popover>
        <PopoverTrigger asChild>
          <button type="button">Open</button>
        </PopoverTrigger>
        <PopoverContent>
          <p>Content</p>
        </PopoverContent>
      </Popover>
    );

    await user.click(screen.getByRole('button', { name: 'Open' }));
    expect(await screen.findByText('Content')).toBeInTheDocument();

    await user.keyboard('{Escape}');
    // After pressing Escape, the popover should close
    await expect(screen.findByText('Content', {}, { timeout: 500 })).rejects.toThrow();
  });

  it('applies custom className to content', async () => {
    const user = userEvent.setup();

    render(
      <Popover>
        <PopoverTrigger asChild>
          <button type="button">Open</button>
        </PopoverTrigger>
        <PopoverContent className="my-custom-class" data-testid="pop-content">
          <p>Content</p>
        </PopoverContent>
      </Popover>
    );

    await user.click(screen.getByRole('button', { name: 'Open' }));
    const content = await screen.findByTestId('pop-content');
    expect(content.className).toContain('my-custom-class');
  });

  it('supports PopoverClose to close the popover', async () => {
    const user = userEvent.setup();

    render(
      <Popover>
        <PopoverTrigger asChild>
          <button type="button">Open</button>
        </PopoverTrigger>
        <PopoverContent>
          <p>Body</p>
          <PopoverClose asChild>
            <button type="button">Close</button>
          </PopoverClose>
        </PopoverContent>
      </Popover>
    );

    await user.click(screen.getByRole('button', { name: 'Open' }));
    expect(await screen.findByText('Body')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Close' }));
    await expect(screen.findByText('Body', {}, { timeout: 500 })).rejects.toThrow();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <Popover>
        <PopoverTrigger asChild>
          <button type="button">Open popover</button>
        </PopoverTrigger>
        <PopoverContent>
          <p>Popover body</p>
        </PopoverContent>
      </Popover>
    );
    await expectNoA11yViolations(container);
  });
});
