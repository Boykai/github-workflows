import { describe, expect, it, vi } from 'vitest';
import { QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import type { ReactElement } from 'react';
import { createTestQueryClient, render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { PipelineBoard } from './PipelineBoard';
import type { PipelineStage, PipelineAgentNode } from '@/types';

function createStage(overrides: Partial<PipelineStage> = {}): PipelineStage {
  return {
    id: 'stage-1',
    name: 'Ready',
    order: 0,
    agents: [],
    ...overrides,
  };
}

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

function renderPipelineBoard(ui: ReactElement) {
  const queryClient = createTestQueryClient();

  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

describe('PipelineBoard', () => {
  it('shows a pipeline name input while editing an existing pipeline', () => {
    renderPipelineBoard(
      <PipelineBoard
        columnCount={1}
        stages={[createStage()]}
        availableAgents={[]}
        availableModels={[]}
        isEditMode={true}
        pipelineName="Advanced Pipeline"
        projectId="project-1"
        modelOverride={{ mode: 'auto', modelId: '', modelName: '' }}
        validationErrors={{}}
        onNameChange={vi.fn()}
        onModelOverrideChange={vi.fn()}
        onClearValidationError={vi.fn()}
        onRemoveStage={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onUpdateStage={vi.fn()}
        onReorderAgents={vi.fn()}
      />
    );

    expect(screen.getByLabelText('Pipeline name')).toHaveValue('Advanced Pipeline');
  });

  it('sets aria-invalid and aria-describedby when a name validation error exists', () => {
    render(
      <PipelineBoard
        columnCount={1}
        stages={[createStage()]}
        availableAgents={[]}
        availableModels={[]}
        isEditMode={true}
        pipelineName="Bad Pipeline"
        projectId="project-1"
        modelOverride={{ mode: 'auto', modelId: '', modelName: '' }}
        validationErrors={{ name: 'Name is required' }}
        onNameChange={vi.fn()}
        onModelOverrideChange={vi.fn()}
        onClearValidationError={vi.fn()}
        onRemoveStage={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onUpdateStage={vi.fn()}
      />
    );

    const input = screen.getByLabelText('Pipeline name');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'pipeline-name-error');

    const errorText = screen.getByText('Name is required');
    expect(errorText).toHaveAttribute('id', 'pipeline-name-error');
  });

  it('does not set aria-invalid when there is no validation error', () => {
    render(
      <PipelineBoard
        columnCount={1}
        stages={[createStage()]}
        availableAgents={[]}
        availableModels={[]}
        isEditMode={true}
        pipelineName="Good Pipeline"
        projectId="project-1"
        modelOverride={{ mode: 'auto', modelId: '', modelName: '' }}
        validationErrors={{}}
        onNameChange={vi.fn()}
        onModelOverrideChange={vi.fn()}
        onClearValidationError={vi.fn()}
        onRemoveStage={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onUpdateStage={vi.fn()}
      />
    );

    const input = screen.getByLabelText('Pipeline name');
    expect(input).not.toHaveAttribute('aria-invalid');
    expect(input).not.toHaveAttribute('aria-describedby');
  });

  it('commits a renamed pipeline name from the edit input', async () => {
    const onNameChange = vi.fn();

    renderPipelineBoard(
      <PipelineBoard
        columnCount={1}
        stages={[createStage()]}
        availableAgents={[]}
        availableModels={[]}
        isEditMode={true}
        pipelineName="Advanced Pipeline"
        projectId="project-1"
        modelOverride={{ mode: 'auto', modelId: '', modelName: '' }}
        validationErrors={{}}
        onNameChange={onNameChange}
        onModelOverrideChange={vi.fn()}
        onClearValidationError={vi.fn()}
        onRemoveStage={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onUpdateStage={vi.fn()}
        onReorderAgents={vi.fn()}
      />
    );

    const user = userEvent.setup();
    const input = screen.getByLabelText('Pipeline name');

    await user.clear(input);
    await user.type(input, 'Renamed Pipeline{Enter}');

    expect(onNameChange).toHaveBeenCalledWith('Renamed Pipeline');
  });

  it('shows the parallel groups helper and widens the stage grid when a group has multiple agents', () => {
    renderPipelineBoard(
      <PipelineBoard
        columnCount={1}
        stages={[createStage({
          groups: [{
            id: 'g1',
            order: 0,
            execution_mode: 'parallel',
            agents: [createAgentNode(), createAgentNode({ id: 'agent-2' })],
          }],
          agents: [],
        })]}
        availableAgents={[]}
        availableModels={[]}
        isEditMode={true}
        pipelineName="Advanced Pipeline"
        projectId="project-1"
        modelOverride={{ mode: 'auto', modelId: '', modelName: '' }}
        validationErrors={{}}
        onNameChange={vi.fn()}
        onModelOverrideChange={vi.fn()}
        onClearValidationError={vi.fn()}
        onRemoveStage={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onUpdateStage={vi.fn()}
        onReorderAgents={vi.fn()}
      />
    );

    expect(screen.getByText('Parallel groups')).toBeInTheDocument();
    expect(screen.getByTestId('pipeline-stage-grid')).toHaveStyle({
      gridTemplateColumns: 'repeat(1, minmax(20rem, 1fr))',
    });
  });

  it('has no accessibility violations', async () => {
    const { container } = renderPipelineBoard(
      <PipelineBoard
        columnCount={1}
        stages={[createStage()]}
        availableAgents={[]}
        availableModels={[]}
        isEditMode={true}
        pipelineName="Test Pipeline"
        projectId="project-1"
        modelOverride={{ mode: 'auto', modelId: '', modelName: '' }}
        validationErrors={{}}
        onNameChange={vi.fn()}
        onModelOverrideChange={vi.fn()}
        onClearValidationError={vi.fn()}
        onRemoveStage={vi.fn()}
        onAddAgent={vi.fn()}
        onRemoveAgent={vi.fn()}
        onUpdateAgent={vi.fn()}
        onUpdateStage={vi.fn()}
        onReorderAgents={vi.fn()}
      />
    );

    await expectNoA11yViolations(container);
  });
});
