import { describe, expect, it, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '@/test/test-utils';
import { AgentTile } from './AgentTile';
import { AgentDragOverlay } from './AgentDragOverlay';
import type { AgentAssignment, AvailableAgent } from '@/types';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

function createAgentAssignment(overrides: Partial<AgentAssignment> = {}): AgentAssignment {
  return {
    id: 'agent-instance-1',
    slug: 'reviewer',
    display_name: 'Reviewer',
    config: null,
    ...overrides,
  };
}

function createAvailableAgent(overrides: Partial<AvailableAgent> = {}): AvailableAgent {
  return {
    slug: 'reviewer',
    display_name: 'Reviewer',
    description: 'Reviews work',
    default_model_id: 'gpt-5-mini',
    default_model_name: 'GPT-5 Mini',
    tools_count: 2,
    source: 'repository',
    ...overrides,
  };
}

describe('AgentTile', () => {
  it('renders the assigned pipeline model in preference to the agent default', () => {
    const agent = createAgentAssignment({
      config: {
        model_id: 'gpt-5.4',
        model_name: 'GPT-5.4',
      },
    });

    render(<AgentTile agent={agent} availableAgents={[createAvailableAgent()]} />);

    expect(screen.getByText(/GPT-5.4/)).toBeInTheDocument();
    expect(screen.queryByText(/GPT-5 Mini/)).not.toBeInTheDocument();
  });

  it('falls back to the agent default model when no pipeline-specific model is assigned', () => {
    render(
      <AgentTile
        agent={createAgentAssignment()}
        availableAgents={[createAvailableAgent({ default_model_name: 'GPT-5 Mini' })]}
      />
    );

    expect(screen.getByText(/GPT-5 Mini/)).toBeInTheDocument();
  });

  it('stops pointerdown from interactive controls reaching the sortable container', () => {
    const onPointerDown = vi.fn();

    render(
      <AgentTile
        agent={createAgentAssignment()}
        onRemove={vi.fn()}
        sortableProps={{
          attributes: {},
          listeners: { onPointerDown },
          setNodeRef: vi.fn(),
          style: {},
          isDragging: false,
        }}
      />
    );

    fireEvent.pointerDown(screen.getByRole('button', { name: 'Remove Reviewer' }));

    expect(onPointerDown).not.toHaveBeenCalled();
  });

  it('stops pointerdown on compact tile controls reaching the sortable container', () => {
    const onPointerDown = vi.fn();

    render(
      <AgentTile
        agent={createAgentAssignment()}
        onRemove={vi.fn()}
        variant="compact"
        sortableProps={{
          attributes: {},
          listeners: { onPointerDown },
          setNodeRef: vi.fn(),
          style: {},
          isDragging: false,
        }}
      />
    );

    fireEvent.pointerDown(screen.getByRole('button', { name: 'Remove Reviewer' }));

    expect(onPointerDown).not.toHaveBeenCalled();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <div role="list">
        <AgentTile agent={createAgentAssignment()} availableAgents={[createAvailableAgent()]} />
      </div>
    );
    await expectNoA11yViolations(container);
  });
});

describe('AgentDragOverlay', () => {
  it('uses the assigned pipeline model in the drag preview metadata', () => {
    const agent = createAgentAssignment({
      config: {
        model_id: 'gpt-5.4',
        model_name: 'GPT-5.4',
      },
    });

    render(<AgentDragOverlay agent={agent} availableAgents={[createAvailableAgent()]} />);

    expect(screen.getByText(/GPT-5.4/)).toBeInTheDocument();
    expect(screen.queryByText(/GPT-5 Mini/)).not.toBeInTheDocument();
  });
});
