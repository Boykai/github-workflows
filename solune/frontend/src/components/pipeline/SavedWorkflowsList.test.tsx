import { describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen, within } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { SavedWorkflowsList } from './SavedWorkflowsList';
import type { PipelineConfigSummary } from '@/types';

function createPipeline(overrides: Partial<PipelineConfigSummary> = {}): PipelineConfigSummary {
  return {
    id: 'pipeline-1',
    name: 'Project Solune Long Pipeline Name That Needs Full Tooltip Visibility',
    description: 'Routes issues through design and build stages.',
    stage_count: 2,
    agent_count: 3,
    total_tool_count: 1,
    is_preset: false,
    preset_id: '',
    updated_at: '2026-03-10T18:30:00Z',
    stages: [
      {
        id: 'stage-1',
        name: 'Ready',
        order: 0,
        agents: [],
      },
    ],
    ...overrides,
  };
}

describe('SavedWorkflowsList', () => {
  it('exposes the saved workflows section for the hero anchor link', () => {
    const { container } = render(
      <SavedWorkflowsList
        pipelines={[]}
        activePipelineId={null}
        assignedPipelineId=""
        isLoading={false}
        onSelect={vi.fn()}
      />
    );

    const section = container.querySelector('#saved-pipelines');
    expect(section).toBeInTheDocument();
    expect(section).toHaveAttribute('aria-labelledby', 'saved-pipelines-title');
    expect(screen.getByRole('heading', { name: 'Saved Pipelines' })).toHaveAttribute(
      'id',
      'saved-pipelines-title'
    );
  });

  it('renders structured skeleton cards while loading', () => {
    const { container } = render(
      <SavedWorkflowsList
        pipelines={[]}
        activePipelineId={null}
        assignedPipelineId=""
        isLoading={true}
        onSelect={vi.fn()}
      />
    );

    const skeletonCards = container.querySelectorAll('.animate-pulse');
    expect(skeletonCards).toHaveLength(3);

    // Each skeleton should contain placeholder shapes (not be a flat empty block)
    for (const card of skeletonCards) {
      expect(card.children.length).toBeGreaterThan(0);
    }
  });

  it('shows the full pipeline name in a tooltip for truncated cards', async () => {
    const user = userEvent.setup();
    const pipeline = createPipeline();

    render(
      <SavedWorkflowsList
        pipelines={[pipeline]}
        activePipelineId={null}
        assignedPipelineId=""
        isLoading={false}
        onSelect={vi.fn()}
      />
    );

    await user.hover(screen.getByText(pipeline.name));

    const tooltip = await screen.findByRole('tooltip');
    expect(tooltip).toBeInTheDocument();
    expect(within(tooltip).getByText(pipeline.name)).toBeInTheDocument();
  });

  it('copies a saved pipeline without selecting the card', async () => {
    const user = userEvent.setup();
    const pipeline = createPipeline();
    const onSelect = vi.fn();
    const onCopy = vi.fn();

    render(
      <SavedWorkflowsList
        pipelines={[pipeline]}
        activePipelineId={null}
        assignedPipelineId=""
        isLoading={false}
        onSelect={onSelect}
        onCopy={onCopy}
      />
    );

    await user.click(screen.getByRole('button', { name: 'Copy' }));

    expect(onCopy).toHaveBeenCalledWith(pipeline.id);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <SavedWorkflowsList
        pipelines={[createPipeline()]}
        activePipelineId={null}
        assignedPipelineId=""
        isLoading={false}
        onSelect={vi.fn()}
      />
    );

    await expectNoA11yViolations(container);
  });
});
