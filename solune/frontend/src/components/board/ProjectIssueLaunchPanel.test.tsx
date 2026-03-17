import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { ProjectIssueLaunchPanel } from './ProjectIssueLaunchPanel';
import { pipelinesApi } from '@/services/api';
import type { PipelineConfigSummary } from '@/types';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

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
    localStorage.removeItem('parentIssueIntake_expanded');
  });

  afterEach(() => {
    localStorage.removeItem('parentIssueIntake_expanded');
  });

  /** Expand the collapsed-by-default panel so the form fields become accessible. */
  async function expandPanel() {
    await userEvent.click(screen.getByRole('button', { name: /parent issue intake/i }));
  }

  describe('collapse / expand', () => {
    it('renders collapsed by default — header visible, form body hidden', () => {
      renderPanel(
        <ProjectIssueLaunchPanel
          projectId="PVT_1"
          pipelines={PIPELINES}
          isLoadingPipelines={false}
          pipelinesError={null}
          onRetryPipelines={vi.fn()}
        />
      );

      const toggle = screen.getByRole('button', { name: /parent issue intake/i });
      expect(toggle).toHaveAttribute('aria-expanded', 'false');
      expect(screen.getByText('Parent issue intake')).toBeInTheDocument();
    });

    it('expands when the header is clicked and collapses again on a second click', async () => {
      renderPanel(
        <ProjectIssueLaunchPanel
          projectId="PVT_1"
          pipelines={PIPELINES}
          isLoadingPipelines={false}
          pipelinesError={null}
          onRetryPipelines={vi.fn()}
        />
      );

      const toggle = screen.getByRole('button', { name: /parent issue intake/i });

      await userEvent.click(toggle);
      expect(toggle).toHaveAttribute('aria-expanded', 'true');

      await userEvent.click(toggle);
      expect(toggle).toHaveAttribute('aria-expanded', 'false');
    });

    it('persists expanded state to localStorage', async () => {
      renderPanel(
        <ProjectIssueLaunchPanel
          projectId="PVT_1"
          pipelines={PIPELINES}
          isLoadingPipelines={false}
          pipelinesError={null}
          onRetryPipelines={vi.fn()}
        />
      );

      expect(localStorage.getItem('parentIssueIntake_expanded')).toBeNull();

      await userEvent.click(screen.getByRole('button', { name: /parent issue intake/i }));
      expect(localStorage.getItem('parentIssueIntake_expanded')).toBe('true');

      await userEvent.click(screen.getByRole('button', { name: /parent issue intake/i }));
      expect(localStorage.getItem('parentIssueIntake_expanded')).toBe('false');
    });

    it('restores expanded state from localStorage on mount', () => {
      localStorage.setItem('parentIssueIntake_expanded', 'true');

      renderPanel(
        <ProjectIssueLaunchPanel
          projectId="PVT_1"
          pipelines={PIPELINES}
          isLoadingPipelines={false}
          pipelinesError={null}
          onRetryPipelines={vi.fn()}
        />
      );

      expect(screen.getByRole('button', { name: /parent issue intake/i })).toHaveAttribute(
        'aria-expanded',
        'true'
      );
    });
  });

  it('shows inline validation and launches the selected pipeline after correction', async () => {
    const onLaunchedMock = vi.fn();
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
        onLaunched={onLaunchedMock}
      />
    );

    await expandPanel();

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
    expect(onLaunchedMock).toHaveBeenCalledWith(
      expect.objectContaining({ success: true, issue_number: 42 })
    );
  });

  it('preserves the entered description and selected pipeline across validation errors', async () => {
    const user = userEvent.setup();

    renderPanel(
      <ProjectIssueLaunchPanel
        projectId="PVT_1"
        pipelines={PIPELINES}
        isLoadingPipelines={false}
        pipelinesError={null}
        onRetryPipelines={vi.fn()}
      />
    );

    await expandPanel();

    const descriptionField = screen.getByLabelText('GitHub Parent Issue Description');
    const pipelineSelect = screen.getByLabelText('Agent Pipeline Config');

    await user.type(descriptionField, 'Keep this parent issue context.');
    await user.click(screen.getByRole('button', { name: 'Launch pipeline' }));

    expect(
      screen.getByText('Select an Agent Pipeline Config before launching.')
    ).toBeInTheDocument();
    expect(descriptionField).toHaveValue('Keep this parent issue context.');

    await user.selectOptions(pipelineSelect, 'pipe-1');
    await user.clear(descriptionField);
    await user.click(screen.getByRole('button', { name: 'Launch pipeline' }));

    expect(
      screen.getByText('Paste or upload the parent issue description first.')
    ).toBeInTheDocument();
    expect(pipelineSelect).toHaveValue('pipe-1');
    expect(mockLaunch).not.toHaveBeenCalled();
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

    await expandPanel();

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

    await expandPanel();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['binary'], 'issue.png', { type: 'image/png' });
    const user = userEvent.setup({ applyAccept: false });

    await user.upload(fileInput, file);

    expect(
      screen.getByText(
        'Only Markdown (.md), plain-text (.txt), WebVTT (.vtt), and SubRip (.srt) files are supported.'
      )
    ).toBeInTheDocument();
    expect(mockLaunch).not.toHaveBeenCalled();
  });

  it('shows launch failures without clearing the form so the user can retry', async () => {
    const onLaunchedMock = vi.fn();
    const user = userEvent.setup();
    mockLaunch.mockResolvedValue({
      success: false,
      issue_number: 84,
      issue_url: 'https://github.com/owner/repo/issues/84',
      message: 'The selected pipeline could not be started.',
    });

    renderPanel(
      <ProjectIssueLaunchPanel
        projectId="PVT_1"
        pipelines={PIPELINES}
        isLoadingPipelines={false}
        pipelinesError={null}
        onRetryPipelines={vi.fn()}
        onLaunched={onLaunchedMock}
      />
    );

    await expandPanel();

    await user.type(screen.getByLabelText('GitHub Parent Issue Description'), '# Retry me');
    await user.selectOptions(screen.getByLabelText('Agent Pipeline Config'), 'pipe-1');
    await user.click(screen.getByRole('button', { name: 'Launch pipeline' }));

    expect(await screen.findByText('Launch failed')).toBeInTheDocument();
    expect(screen.getByText('The selected pipeline could not be started.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open the created issue' })).toHaveAttribute(
      'href',
      'https://github.com/owner/repo/issues/84'
    );
    expect(screen.getByLabelText('GitHub Parent Issue Description')).toHaveValue('# Retry me');
    expect(screen.getByLabelText('Agent Pipeline Config')).toHaveValue('pipe-1');
    expect(onLaunchedMock).not.toHaveBeenCalled();
  });

  it('renders the pipeline loading error state and retries on request', async () => {
    const onRetryPipelines = vi.fn();
    const user = userEvent.setup();

    renderPanel(
      <ProjectIssueLaunchPanel
        projectId="PVT_1"
        pipelines={PIPELINES}
        isLoadingPipelines={false}
        pipelinesError="Could not load pipeline configs."
        onRetryPipelines={onRetryPipelines}
      />
    );

    await expandPanel();

    expect(screen.getByText('Could not load pipeline configs.')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Retry loading configs' }));

    expect(onRetryPipelines).toHaveBeenCalledTimes(1);
  });

  it('has no accessibility violations', async () => {
    const { container } = renderPanel(
      <ProjectIssueLaunchPanel
        projectId="PVT_1"
        pipelines={PIPELINES}
        isLoadingPipelines={false}
        pipelinesError={null}
        onRetryPipelines={vi.fn()}
      />
    );
    await expectNoA11yViolations(container);
  });
});
