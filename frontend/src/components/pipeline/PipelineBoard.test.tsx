import { describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@/test/test-utils';
import { PipelineBoard } from './PipelineBoard';
import type { PipelineStage } from '@/types';

function createStage(overrides: Partial<PipelineStage> = {}): PipelineStage {
  return {
    id: 'stage-1',
    name: 'Ready',
    order: 0,
    agents: [],
    ...overrides,
  };
}

describe('PipelineBoard', () => {
  it('shows a pipeline name input while editing an existing pipeline', () => {
    render(
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
      />
    );

    expect(screen.getByLabelText('Pipeline name')).toHaveValue('Advanced Pipeline');
  });

  it('commits a renamed pipeline name from the edit input', async () => {
    const onNameChange = vi.fn();

    render(
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
      />
    );

    const user = userEvent.setup();
    const input = screen.getByLabelText('Pipeline name');

    await user.clear(input);
    await user.type(input, 'Renamed Pipeline{Enter}');

    expect(onNameChange).toHaveBeenCalledWith('Renamed Pipeline');
  });
});
