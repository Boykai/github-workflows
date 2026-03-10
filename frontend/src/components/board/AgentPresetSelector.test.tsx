import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { within } from '@testing-library/react';
import type { ReactNode } from 'react';

import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { AgentPresetSelector } from './AgentPresetSelector';

const mockPipelinesList = vi.fn();
const mockPipelinesGet = vi.fn();

vi.mock('@/services/api', () => ({
  pipelinesApi: {
    list: (...args: unknown[]) => mockPipelinesList(...args),
    get: (...args: unknown[]) => mockPipelinesGet(...args),
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ConfirmationDialogProvider>{children}</ConfirmationDialogProvider>
      </QueryClientProvider>
    );
  };
}

describe('AgentPresetSelector', () => {
  const onApplyPreset = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockPipelinesList.mockResolvedValue({
      pipelines: [
        {
          id: 'pipeline-1',
          name: 'Release Flow',
          stage_count: 3,
          agent_count: 4,
        },
      ],
    });
  });

  it('uses the shared confirmation dialog for built-in presets', async () => {
    const user = userEvent.setup();

    render(
      <AgentPresetSelector
        columnNames={['Backlog', 'In Progress', 'In Review']}
        currentMappings={{ Backlog: [], 'In Progress': [], 'In Review': [] }}
        onApplyPreset={onApplyPreset}
        projectId="project-1"
      />,
      { wrapper: createWrapper() }
    );

    await user.click(screen.getByRole('button', { name: 'Clear' }));

    const dialog = await screen.findByRole('dialog');
    expect(dialog).toHaveAttribute('aria-labelledby', 'confirmation-dialog-title');
    expect(screen.getByText('Clear pipeline assignments?')).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: 'Clear' })).toBeInTheDocument();
  });

  it('shows shared dialog error feedback when applying a saved pipeline fails', async () => {
    const user = userEvent.setup();
    mockPipelinesGet.mockRejectedValue(new Error('Failed to load and apply the selected pipeline.'));

    render(
      <AgentPresetSelector
        columnNames={['Backlog', 'In Progress', 'In Review']}
        currentMappings={{ Backlog: [], 'In Progress': [], 'In Review': [] }}
        onApplyPreset={onApplyPreset}
        projectId="project-1"
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /saved/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /saved/i }));
    await user.click(screen.getByRole('button', { name: /release flow/i }));
    await user.click(await screen.findByRole('button', { name: 'Apply Pipeline' }));

    await waitFor(() => {
      expect(screen.getByText('Failed to load and apply the selected pipeline.')).toBeInTheDocument();
    });
    expect(onApplyPreset).not.toHaveBeenCalled();
  });
});
