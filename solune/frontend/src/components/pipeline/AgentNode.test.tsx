import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import userEvent from '@testing-library/user-event';
import { AgentNode } from './AgentNode';
import type { PipelineAgentNode } from '@/types';

const mockUseModels = vi.fn();

vi.mock('@/hooks/useModels', () => ({
  useModels: (...args: unknown[]) => mockUseModels(...args),
}));

function createAgentNode(overrides: Partial<PipelineAgentNode> = {}): PipelineAgentNode {
  return {
    id: 'agent-node-1',
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

describe('AgentNode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseModels.mockReturnValue({
      models: [
        { id: 'gpt-5.4', name: 'GPT-5.4', provider: 'GitHub Models' },
        { id: 'gpt-5.4-mini', name: 'GPT-5.4 Mini', provider: 'GitHub Models' },
      ],
      modelsByProvider: [
        {
          provider: 'GitHub Models',
          models: [
            { id: 'gpt-5.4', name: 'GPT-5.4', provider: 'GitHub Models' },
            { id: 'gpt-5.4-mini', name: 'GPT-5.4 Mini', provider: 'GitHub Models' },
          ],
        },
      ],
      isLoading: false,
      isRefreshing: false,
      refreshModels: vi.fn(),
      error: null,
    });
  });

  it('shows an explicit model control for pipeline agents', () => {
    render(<AgentNode agentNode={createAgentNode()} onModelSelect={vi.fn()} onRemove={vi.fn()} />);

    expect(screen.getByText('Model')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /auto/i })).toBeInTheDocument();
  });

  it('lets the user change the model from the pipeline agent card', async () => {
    const onModelSelect = vi.fn();
    render(
      <AgentNode agentNode={createAgentNode()} onModelSelect={onModelSelect} onRemove={vi.fn()} />
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /auto/i }));
    await user.click(screen.getByRole('button', { name: /^gpt-5\.4$/i }));

    expect(onModelSelect).toHaveBeenCalledWith('gpt-5.4', 'GPT-5.4');
  });

  it('stops pointerdown from interactive controls reaching the drag listener', () => {
    const onPointerDown = vi.fn();

    render(
      <AgentNode
        agentNode={createAgentNode()}
        onModelSelect={vi.fn()}
        onRemove={vi.fn()}
        dragHandleListeners={{ onPointerDown } as never}
      />
    );

    fireEvent.pointerDown(screen.getByRole('button', { name: /auto/i }));
    fireEvent.pointerDown(screen.getByRole('button', { name: 'Remove agent' }));

    expect(onPointerDown).not.toHaveBeenCalled();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(
      <AgentNode agentNode={createAgentNode()} onModelSelect={vi.fn()} onRemove={vi.fn()} />
    );

    await expectNoA11yViolations(container);
  });
});
