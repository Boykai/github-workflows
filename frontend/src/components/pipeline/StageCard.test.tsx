import { describe, expect, it, vi } from 'vitest';
import { QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import type { ReactElement } from 'react';
import { createTestQueryClient, render, screen } from '@/test/test-utils';
import { StageCard } from './StageCard';
import type { PipelineStage, AvailableAgent, PipelineAgentNode, ExecutionGroup } from '@/types';

function createAgentNode(overrides: Partial<PipelineAgentNode> = {}): PipelineAgentNode {
  return {
    id: 'agent-1',
    agent_slug: 'copilot',
    agent_display_name: 'GitHub Copilot',
    model_id: '',
    model_name: '',
    tool_ids: [],
    tool_count: 0,
    config: {},
    ...overrides,
  };
}

function createGroup(overrides: Partial<ExecutionGroup> = {}): ExecutionGroup {
  return {
    id: 'group-1',
    order: 0,
    execution_mode: 'sequential',
    agents: [],
    ...overrides,
  };
}

function createStage(overrides: Partial<PipelineStage> = {}): PipelineStage {
  return {
    id: 'stage-1',
    name: 'Ready',
    order: 0,
    agents: [],
    groups: [createGroup()],
    ...overrides,
  };
}

function createAvailableAgent(overrides: Partial<AvailableAgent> = {}): AvailableAgent {
  return {
    slug: 'copilot',
    display_name: 'GitHub Copilot',
    description: 'Default GitHub Copilot coding agent',
    avatar_url: null,
    icon_name: null,
    default_model_id: '',
    default_model_name: '',
    tools_count: 0,
    source: 'builtin',
    ...overrides,
  };
}

function renderStageCard(ui: ReactElement) {
  const queryClient = createTestQueryClient();

  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

describe('StageCard', () => {
  it('shows a loading state while available agents are being fetched', async () => {
    renderStageCard(
      <StageCard
        stage={createStage()}
        availableAgents={[]}
        agentsLoading={true}
        projectId="project-1"
        onUpdate={vi.fn()}
        onRemove={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onReorderAgents={vi.fn()}
      />
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /add agent/i }));

    expect(screen.getByText('Loading agents...')).toBeInTheDocument();
  });

  it('renders available agents in the picker when discovery succeeds', async () => {
    renderStageCard(
      <StageCard
        stage={createStage()}
        availableAgents={[createAvailableAgent()]}
        projectId="project-1"
        onUpdate={vi.fn()}
        onRemove={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onReorderAgents={vi.fn()}
      />
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /add agent/i }));

    expect(screen.getByText('GitHub Copilot')).toBeInTheDocument();
    expect(screen.getByText('(copilot)')).toBeInTheDocument();
  });

  it('renders execution groups within a stage', () => {
    renderStageCard(
      <StageCard
        stage={createStage({
          groups: [
            createGroup({
              id: 'g1',
              execution_mode: 'parallel',
              agents: [
                createAgentNode(),
                createAgentNode({
                  id: 'agent-2',
                  agent_slug: 'reviewer',
                  agent_display_name: 'Reviewer',
                }),
              ],
            }),
          ],
        })}
        availableAgents={[]}
        projectId="project-1"
        onUpdate={vi.fn()}
        onRemove={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onReorderAgents={vi.fn()}
      />
    );

    expect(screen.getByText('Parallel')).toBeInTheDocument();
  });

  it('shows add group button when onAddGroup callback is provided', () => {
    renderStageCard(
      <StageCard
        stage={createStage()}
        availableAgents={[]}
        projectId="project-1"
        onUpdate={vi.fn()}
        onRemove={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onReorderAgents={vi.fn()}
        onAddGroup={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /add execution group/i })).toBeInTheDocument();
  });
});
