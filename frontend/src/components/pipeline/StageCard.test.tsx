import { describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@/test/test-utils';
import { StageCard } from './StageCard';
import type { PipelineStage, AvailableAgent } from '@/types';

function createStage(overrides: Partial<PipelineStage> = {}): PipelineStage {
  return {
    id: 'stage-1',
    name: 'Ready',
    agents: [],
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

describe('StageCard', () => {
  it('shows a loading state while available agents are being fetched', async () => {
    render(
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
      />
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /add agent/i }));

    expect(screen.getByText('Loading agents...')).toBeInTheDocument();
  });

  it('renders available agents in the picker when discovery succeeds', async () => {
    render(
      <StageCard
        stage={createStage()}
        availableAgents={[createAvailableAgent()]}
        projectId="project-1"
        onUpdate={vi.fn()}
        onRemove={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
      />
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /add agent/i }));

    expect(screen.getByText('GitHub Copilot')).toBeInTheDocument();
    expect(screen.getByText('(copilot)')).toBeInTheDocument();
  });
});
