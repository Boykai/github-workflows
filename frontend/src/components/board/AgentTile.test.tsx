/**
 * Unit tests for AgentTile component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentTile } from './AgentTile';
import type { AgentAssignment, AvailableAgent } from '@/types';

function createAgent(overrides: Partial<AgentAssignment> = {}): AgentAssignment {
  return {
    id: 'agent-1',
    slug: 'code-review-bot',
    display_name: 'Code Review Bot',
    ...overrides,
  };
}

function createAvailableAgent(overrides: Partial<AvailableAgent> = {}): AvailableAgent {
  return {
    slug: 'code-review-bot',
    display_name: 'Code Review Bot',
    description: 'Performs automated code reviews',
    source: 'builtin',
    ...overrides,
  };
}

describe('AgentTile', () => {
  it('renders agent display name', () => {
    render(<AgentTile agent={createAgent()} />);
    expect(screen.getByText('Code Review Bot')).toBeDefined();
  });

  it('shows slug when no display_name', () => {
    render(<AgentTile agent={createAgent({ display_name: null })} />);
    expect(screen.getByText('code-review-bot')).toBeDefined();
  });

  it('remove button calls onRemove', () => {
    const onRemove = vi.fn();
    render(<AgentTile agent={createAgent()} onRemove={onRemove} />);
    fireEvent.click(screen.getByTitle('Remove agent'));
    expect(onRemove).toHaveBeenCalledWith('agent-1');
  });

  it('expand/collapse toggle works', () => {
    const availableAgents = [createAvailableAgent()];
    render(<AgentTile agent={createAgent()} availableAgents={availableAgents} />);
    // Initially collapsed - no description shown
    expect(screen.queryByText('Performs automated code reviews')).toBeNull();
    // Expand
    fireEvent.click(screen.getByTitle('Expand'));
    expect(screen.getByText('Performs automated code reviews')).toBeDefined();
    // Collapse
    fireEvent.click(screen.getByTitle('Collapse'));
    expect(screen.queryByText('Performs automated code reviews')).toBeNull();
  });

  it('shows warning badge when isWarning', () => {
    const { container } = render(<AgentTile agent={createAgent()} isWarning />);
    expect(container.querySelector('.agent-tile--warning')).not.toBeNull();
    expect(screen.getByText('⚠')).toBeDefined();
  });

  it('shows metadata description in expanded view', () => {
    const availableAgents = [createAvailableAgent({ description: 'Runs CI pipelines' })];
    render(
      <AgentTile
        agent={createAgent({ slug: 'code-review-bot' })}
        availableAgents={availableAgents}
      />
    );
    fireEvent.click(screen.getByTitle('Expand'));
    expect(screen.getByText('Runs CI pipelines')).toBeDefined();
  });
});
