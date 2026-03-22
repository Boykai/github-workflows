import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { PipelineAnalytics } from './PipelineAnalytics';
import type { PipelineConfigSummary } from '@/types';

// ── Helpers ──

function createPipeline(overrides: Partial<PipelineConfigSummary> = {}): PipelineConfigSummary {
  return {
    id: 'pipe-1',
    name: 'Test Pipeline',
    description: 'A test pipeline',
    stage_count: 2,
    agent_count: 3,
    total_tool_count: 5,
    is_preset: false,
    preset_id: '',
    stages: [
      {
        id: 'stage-1',
        name: 'Stage 1',
        order: 0,
        groups: [
          {
            id: 'group-1',
            name: 'Group 1',
            execution_mode: 'sequential',
            agents: [
              {
                id: 'agent-1',
                agent_slug: 'reviewer',
                agent_display_name: 'Reviewer',
                model_id: 'gpt-5-mini',
                model_name: 'GPT-5 Mini',
                tool_ids: [],
                tool_count: 2,
                config: {},
              },
              {
                id: 'agent-2',
                agent_slug: 'coder',
                agent_display_name: 'Coder',
                model_id: 'gpt-5.4',
                model_name: 'GPT-5.4',
                tool_ids: [],
                tool_count: 3,
                config: {},
              },
            ],
          },
        ],
        agents: [],
      },
    ],
    ...overrides,
  } as PipelineConfigSummary;
}

// ── Tests ──

describe('PipelineAnalytics', () => {
  it('shows empty state when no pipelines are provided', () => {
    render(<PipelineAnalytics pipelines={[]} />);

    expect(
      screen.getByText('Analytics will appear once pipelines are created')
    ).toBeInTheDocument();
  });

  it('displays the total pipeline count', () => {
    render(<PipelineAnalytics pipelines={[createPipeline(), createPipeline({ id: 'pipe-2', name: 'Second' })]} />);

    // The Pipelines stat card should show the count
    expect(screen.getByText('Pipelines')).toBeInTheDocument();
    // Use getAllByText since "2" may appear in multiple stat cards
    const twoElements = screen.getAllByText('2');
    expect(twoElements.length).toBeGreaterThanOrEqual(1);
  });

  it('renders the Pipeline Analytics heading', () => {
    render(<PipelineAnalytics pipelines={[createPipeline()]} />);

    expect(screen.getByText('Pipeline Analytics')).toBeInTheDocument();
  });

  it('shows agent distribution for top agents', () => {
    render(<PipelineAnalytics pipelines={[createPipeline()]} />);

    expect(screen.getByText('Most Used Agents')).toBeInTheDocument();
    // Agent names rendered via formatAgentName — the display name should appear
    expect(screen.getByText(/Reviewer/)).toBeInTheDocument();
    expect(screen.getByText(/Coder/)).toBeInTheDocument();
  });

  it('shows model distribution section', () => {
    render(<PipelineAnalytics pipelines={[createPipeline()]} />);

    expect(screen.getByText('Model Distribution')).toBeInTheDocument();
    expect(screen.getByText('GPT-5 Mini')).toBeInTheDocument();
    expect(screen.getByText('GPT-5.4')).toBeInTheDocument();
  });
});
