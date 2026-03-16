/**
 * Component tests for CommandAutocomplete.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { CommandAutocomplete } from './CommandAutocomplete';
import { createCommandDefinition } from '@/test/factories';

const mockCommands = [
  createCommandDefinition({ name: 'help', description: 'Show all commands', syntax: '/help' }),
  createCommandDefinition({ name: 'theme', description: 'Change theme', syntax: '/theme <value>' }),
  createCommandDefinition({
    name: 'view',
    description: 'Set default view',
    syntax: '/view <value>',
  }),
];

describe('CommandAutocomplete', () => {
  it('renders all commands when provided', () => {
    render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={0}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );

    expect(screen.getByText('/help')).toBeTruthy();
    expect(screen.getByText('/theme')).toBeTruthy();
    expect(screen.getByText('/view')).toBeTruthy();
  });

  it('shows command description', () => {
    render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={0}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );

    expect(screen.getByText('Show all commands')).toBeTruthy();
    expect(screen.getByText('Change theme')).toBeTruthy();
  });

  it('highlights the correct item', () => {
    render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={1}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );

    const options = screen.getAllByRole('option');
    expect(options[1].getAttribute('aria-selected')).toBe('true');
    expect(options[0].getAttribute('aria-selected')).toBe('false');
  });

  it('calls onSelect on mouse click', () => {
    const onSelect = vi.fn();
    render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={0}
        onSelect={onSelect}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );

    const options = screen.getAllByRole('option');
    fireEvent.mouseDown(options[1]);
    expect(onSelect).toHaveBeenCalledWith(mockCommands[1]);
  });

  it('renders nothing when commands array is empty', () => {
    const { container } = render(
      <CommandAutocomplete
        commands={[]}
        highlightedIndex={0}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );

    expect(container.innerHTML).toBe('');
  });

  it('has role="listbox" for accessibility', () => {
    render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={0}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );

    expect(screen.getByRole('listbox')).toBeTruthy();
  });

  it('items have role="option"', () => {
    render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={0}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );

    const options = screen.getAllByRole('option');
    expect(options.length).toBe(3);
  });

  it('calls onHighlightChange on mouse enter', () => {
    const onHighlightChange = vi.fn();
    render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={0}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={onHighlightChange}
      />
    );

    const options = screen.getAllByRole('option');
    fireEvent.mouseEnter(options[2]);
    expect(onHighlightChange).toHaveBeenCalledWith(2);
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <CommandAutocomplete
        commands={mockCommands}
        highlightedIndex={0}
        onSelect={vi.fn()}
        onDismiss={vi.fn()}
        onHighlightChange={vi.fn()}
      />
    );
    await expectNoA11yViolations(container);
  });
});
