import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { PipelineFlowGraph } from './PipelineFlowGraph';
import type { PipelineStage } from '@/types';

function createStages(): PipelineStage[] {
  return [
    {
      id: 'stage-1',
      name: 'Backlog',
      order: 0,
      agents: [
        {
          id: 'agent-1',
          agent_slug: 'speckit.specify',
          agent_display_name: 'Spec Writer',
          model_id: '',
          model_name: '',
          tool_ids: [],
          tool_count: 0,
          config: {},
        },
      ],
    },
    {
      id: 'stage-2',
      name: 'Ready',
      order: 1,
      agents: [
        {
          id: 'agent-2',
          agent_slug: 'speckit.plan',
          agent_display_name: 'Planner',
          model_id: '',
          model_name: '',
          tool_ids: [],
          tool_count: 0,
          config: {},
        },
        {
          id: 'agent-3',
          agent_slug: 'speckit.tasks',
          agent_display_name: 'Task Generator',
          model_id: '',
          model_name: '',
          tool_ids: [],
          tool_count: 0,
          config: {},
        },
      ],
    },
  ];
}

describe('PipelineFlowGraph', () => {
  it('renders themed agent nodes in execution order without visible stage labels', () => {
    render(<PipelineFlowGraph stages={createStages()} width={236} height={118} />);

    expect(screen.queryByText('Backlog')).not.toBeInTheDocument();
    expect(screen.queryByText('Ready')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Backlog: Spec Writer')).toBeInTheDocument();
    expect(screen.getByLabelText('Ready: Planner')).toBeInTheDocument();
    expect(screen.getByLabelText('Ready: Task Generator')).toBeInTheDocument();
  });

  it('renders an empty state when there are no stages', () => {
    render(<PipelineFlowGraph stages={[]} />);

    expect(screen.getByText('No stages')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <PipelineFlowGraph stages={createStages()} width={236} height={118} />
    );

    await expectNoA11yViolations(container);
  });
});
