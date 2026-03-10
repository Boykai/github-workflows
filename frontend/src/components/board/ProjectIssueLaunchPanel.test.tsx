import { describe, expect, it, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { ProjectIssueLaunchPanel } from './ProjectIssueLaunchPanel';
import { pipelinesApi } from '@/services/api';
import type { PipelineConfigSummary } from '@/types';

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    pipelinesApi: {
      ...actual.pipelinesApi,
      launch: vi.fn(),
    },
  };
});

const mockLaunch = vi.mocked(pipelinesApi.launch);

const PIPELINES: PipelineConfigSummary[] = [
  {
    id: 'pipe-1',
    name: 'Spec Kit Flow',
    description: 'Default spec workflow',
    stage_count: 4,
    agent_count: 6,
    total_tool_count: 0,
    is_preset: false,
    preset_id: '',
    stages: [],
    blocking: false,
    updated_at: '2026-03-10T00:00:00Z',
  },
];

function renderPanel(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

describe('ProjectIssueLaunchPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows inline validation and launches the selected pipeline after correction', async () => {
    const launched = vi.fn();
    mockLaunch.mockResolvedValue({
      success: true,
      issue_number: 42,
      issue_url: 'https://github.com/owner/repo/issues/42',
      message: 'Issue #42 created and launched.',
    });

    renderPanel(
      <ProjectIssueLaunchPanel
        projectId="PVT_1"
        projectName="Solune"
        pipelines={PIPELINES}
        isLoadingPipelines={false}
        pipelinesError={null}
        onRetryPipelines={vi.fn()}
        onLaunched={launched}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: 'Launch pipeline' }));

    expect(
      screen.getByText('Paste or upload the parent issue description first.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Select an Agent Pipeline Config before launching.')
    ).toBeInTheDocument();

    await userEvent.type(
      screen.getByLabelText('GitHub Parent Issue Description'),
      '# Import existing issue\n\nPreserve this parent issue context.'
    );
    await userEvent.selectOptions(screen.getByLabelText('Agent Pipeline Config'), 'pipe-1');
    await userEvent.click(screen.getByRole('button', { name: 'Launch pipeline' }));

    await waitFor(() => {
      expect(mockLaunch).toHaveBeenCalledWith('PVT_1', {
        issue_description: '# Import existing issue\n\nPreserve this parent issue context.',
        pipeline_id: 'pipe-1',
      });
    });

    expect(screen.getByText('Pipeline launched successfully')).toBeInTheDocument();
    expect(launched).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, issue_number: 42 })
    );
  });

  it('imports supported markdown files into the textarea', async () => {
    renderPanel(
      <ProjectIssueLaunchPanel
        projectId="PVT_1"
        pipelines={PIPELINES}
        isLoadingPipelines={false}
        pipelinesError={null}
        onRetryPipelines={vi.fn()}
      />
    );

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['# Imported issue\n\nLoaded from disk.'], 'issue.md', {
      type: 'text/markdown',
    });

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByLabelText('GitHub Parent Issue Description')).toHaveValue(
        '# Imported issue\n\nLoaded from disk.'
      );
    });
    expect(screen.getByText('Imported issue.md')).toBeInTheDocument();
  });

  it('rejects unsupported files with a clear inline error', async () => {
    renderPanel(
      <ProjectIssueLaunchPanel
        projectId="PVT_1"
        pipelines={PIPELINES}
        isLoadingPipelines={false}
        pipelinesError={null}
        onRetryPipelines={vi.fn()}
      />
    );

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['binary'], 'issue.png', { type: 'image/png' });
    const user = userEvent.setup({ applyAccept: false });

    await user.upload(fileInput, file);

    expect(
      screen.getByText('Only Markdown (.md) and plain-text (.txt) files are supported.')
    ).toBeInTheDocument();
    expect(mockLaunch).not.toHaveBeenCalled();
  });
});
