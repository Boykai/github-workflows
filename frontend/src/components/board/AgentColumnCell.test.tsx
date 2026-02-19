/**
 * Unit tests for AgentColumnCell component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import type { AgentAssignment } from '@/types';

vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  closestCenter: vi.fn(),
  KeyboardSensor: vi.fn(),
  PointerSensor: vi.fn(),
  useSensors: vi.fn(() => []),
  useSensor: vi.fn(),
}));
vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  verticalListSortingStrategy: {},
  useSortable: vi.fn(() => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  })),
  arrayMove: vi.fn((arr: unknown[], from: number, to: number) => {
    const result = [...arr];
    const [moved] = result.splice(from, 1);
    result.splice(to, 0, moved);
    return result;
  }),
  sortableKeyboardCoordinates: vi.fn(),
}));
vi.mock('@dnd-kit/modifiers', () => ({
  restrictToVerticalAxis: {},
}));
vi.mock('@dnd-kit/utilities', () => ({
  CSS: { Transform: { toString: vi.fn(() => '') } },
}));

import { AgentColumnCell } from './AgentColumnCell';

function createAgent(id: string, slug: string, displayName: string): AgentAssignment {
  return { id, slug, display_name: displayName };
}

const defaultProps = {
  status: 'In Progress',
  agents: [] as AgentAssignment[],
  isModified: false,
  onRemoveAgent: vi.fn(),
  onReorderAgents: vi.fn(),
};

describe('AgentColumnCell', () => {
  it('renders agent tiles for each agent', () => {
    const agents = [
      createAgent('a1', 'bot-a', 'Bot A'),
      createAgent('a2', 'bot-b', 'Bot B'),
    ];
    render(<AgentColumnCell {...defaultProps} agents={agents} />);
    expect(screen.getByText('Bot A')).toBeDefined();
    expect(screen.getByText('Bot B')).toBeDefined();
  });

  it('shows modified class when isModified', () => {
    const { container } = render(<AgentColumnCell {...defaultProps} isModified={true} />);
    expect(container.querySelector('.agent-column-cell--modified')).not.toBeNull();
  });

  it('does not show modified class when not modified', () => {
    const { container } = render(<AgentColumnCell {...defaultProps} isModified={false} />);
    expect(container.querySelector('.agent-column-cell--modified')).toBeNull();
  });

  it('renders add button slot', () => {
    render(
      <AgentColumnCell
        {...defaultProps}
        renderAddButton={<button data-testid="add-btn">Add</button>}
      />
    );
    expect(screen.getByTestId('add-btn')).toBeDefined();
  });

  it('shows warning when agent count > 10', () => {
    const agents = Array.from({ length: 11 }, (_, i) =>
      createAgent(`a${i}`, `bot-${i}`, `Bot ${i}`)
    );
    render(<AgentColumnCell {...defaultProps} agents={agents} />);
    expect(screen.getByText(/11 agents assigned/)).toBeDefined();
  });

  it('does not show warning when agent count <= 10', () => {
    const agents = Array.from({ length: 10 }, (_, i) =>
      createAgent(`a${i}`, `bot-${i}`, `Bot ${i}`)
    );
    render(<AgentColumnCell {...defaultProps} agents={agents} />);
    expect(screen.queryByText(/agents assigned/)).toBeNull();
  });

  it('handleRemove calls onRemoveAgent with status and agent id', () => {
    const onRemoveAgent = vi.fn();
    const agents = [createAgent('a1', 'bot-a', 'Bot A')];
    render(<AgentColumnCell {...defaultProps} agents={agents} onRemoveAgent={onRemoveAgent} />);
    const removeBtn = screen.getByTitle('Remove agent');
    fireEvent.click(removeBtn);
    expect(onRemoveAgent).toHaveBeenCalledWith('In Progress', 'a1');
  });

  it('renders with availableAgents and shows warning for unknown agent', () => {
    const agents = [createAgent('a1', 'unknown-bot', 'Unknown Bot')];
    const availableAgents = [
      { slug: 'bot-a', display_name: 'Bot A', source: 'builtin' as const },
    ];
    const { container } = render(
      <AgentColumnCell {...defaultProps} agents={agents} availableAgents={availableAgents} />
    );
    // The SortableAgentTile passes isWarning to AgentTile
    expect(container.querySelector('.agent-tile--warning')).not.toBeNull();
  });

  it('does not show warning when agent is in available agents list', () => {
    const agents = [createAgent('a1', 'bot-a', 'Bot A')];
    const availableAgents = [
      { slug: 'bot-a', display_name: 'Bot A', source: 'builtin' as const },
    ];
    const { container } = render(
      <AgentColumnCell {...defaultProps} agents={agents} availableAgents={availableAgents} />
    );
    expect(container.querySelector('.agent-tile--warning')).toBeNull();
  });

  it('shows warning for 12 agents', () => {
    const agents = Array.from({ length: 12 }, (_, i) =>
      createAgent(`a${i}`, `bot-${i}`, `Bot ${i}`)
    );
    render(<AgentColumnCell {...defaultProps} agents={agents} />);
    expect(screen.getByText(/12 agents assigned/)).toBeDefined();
  });
});
