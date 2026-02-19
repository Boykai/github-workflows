/**
 * Unit tests for AddAgentPopover component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AddAgentPopover } from './AddAgentPopover';
import type { AvailableAgent, AgentAssignment } from '@/types';

function createAvailableAgent(overrides: Partial<AvailableAgent> = {}): AvailableAgent {
  return {
    slug: 'test-agent',
    display_name: 'Test Agent',
    description: 'A test agent',
    source: 'builtin',
    ...overrides,
  };
}

function createAssignment(overrides: Partial<AgentAssignment> = {}): AgentAssignment {
  return {
    id: 'assign-1',
    slug: 'test-agent',
    display_name: 'Test Agent',
    ...overrides,
  };
}

const baseProps = {
  status: 'In Progress',
  availableAgents: [] as AvailableAgent[],
  assignedAgents: [] as AgentAssignment[],
  isLoading: false,
  error: null,
  onRetry: vi.fn(),
  onAddAgent: vi.fn(),
};

describe('AddAgentPopover', () => {
  it('renders trigger button with "Add Agent" text', () => {
    render(<AddAgentPopover {...baseProps} />);
    expect(screen.getByText('+ Add Agent')).toBeDefined();
  });

  it('opens popover on click', () => {
    render(<AddAgentPopover {...baseProps} />);
    fireEvent.click(screen.getByText('+ Add Agent'));
    expect(screen.getByRole('listbox')).toBeDefined();
  });

  it('shows loading state', () => {
    render(<AddAgentPopover {...baseProps} isLoading={true} />);
    fireEvent.click(screen.getByText('+ Add Agent'));
    expect(screen.getByText('Loading agents...')).toBeDefined();
  });

  it('shows error state with retry button', () => {
    const onRetry = vi.fn();
    render(<AddAgentPopover {...baseProps} error="Fetch failed" onRetry={onRetry} />);
    fireEvent.click(screen.getByText('+ Add Agent'));
    expect(screen.getByText('⚠ Fetch failed')).toBeDefined();
    fireEvent.click(screen.getByText('Retry'));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('lists available agents', () => {
    const agents = [
      createAvailableAgent({ slug: 'bot-a', display_name: 'Bot A' }),
      createAvailableAgent({ slug: 'bot-b', display_name: 'Bot B' }),
    ];
    render(<AddAgentPopover {...baseProps} availableAgents={agents} />);
    fireEvent.click(screen.getByText('+ Add Agent'));
    expect(screen.getByText('Bot A')).toBeDefined();
    expect(screen.getByText('Bot B')).toBeDefined();
  });

  it('filters agents by search input', () => {
    const agents = [
      createAvailableAgent({ slug: 'bot-a', display_name: 'Alpha Bot' }),
      createAvailableAgent({ slug: 'bot-b', display_name: 'Beta Bot' }),
    ];
    render(<AddAgentPopover {...baseProps} availableAgents={agents} />);
    fireEvent.click(screen.getByText('+ Add Agent'));
    fireEvent.change(screen.getByPlaceholderText('Filter agents...'), {
      target: { value: 'Alpha' },
    });
    expect(screen.getByText('Alpha Bot')).toBeDefined();
    expect(screen.queryByText('Beta Bot')).toBeNull();
  });

  it('selects agent and calls onAddAgent', () => {
    const onAddAgent = vi.fn();
    const agents = [createAvailableAgent({ slug: 'bot-a', display_name: 'Bot A' })];
    render(<AddAgentPopover {...baseProps} availableAgents={agents} onAddAgent={onAddAgent} />);
    fireEvent.click(screen.getByText('+ Add Agent'));
    fireEvent.click(screen.getByText('Bot A'));
    expect(onAddAgent).toHaveBeenCalledWith('In Progress', agents[0]);
  });

  it('shows "already assigned" badge for duplicates', () => {
    const agents = [createAvailableAgent({ slug: 'bot-a', display_name: 'Bot A' })];
    const assigned = [createAssignment({ slug: 'bot-a' })];
    render(
      <AddAgentPopover {...baseProps} availableAgents={agents} assignedAgents={assigned} />
    );
    fireEvent.click(screen.getByText('+ Add Agent'));
    expect(screen.getByText('already assigned')).toBeDefined();
  });

  it('shows "No agents available" when empty', () => {
    render(<AddAgentPopover {...baseProps} availableAgents={[]} />);
    fireEvent.click(screen.getByText('+ Add Agent'));
    expect(screen.getByText('No agents available')).toBeDefined();
  });
});
