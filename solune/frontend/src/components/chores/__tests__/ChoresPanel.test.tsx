/**
 * Tests for ChoresPanel component.
 *
 * Covers: empty state rendering, chore list rendering, loading state, error state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { ChoresPanel } from '../ChoresPanel';
import { ApiError } from '@/services/api';
import type { Chore } from '@/types';
import type { ReactNode } from 'react';

// ── Mock API ──

const mockList = vi.fn();
const mockListTemplates = vi.fn();
const mockUpdate = vi.fn();
const mockInlineUpdate = vi.fn();
const mockPipelinesList = vi.fn();

vi.mock('@/services/api', () => ({
  choresApi: {
    list: (...args: unknown[]) => mockList(...args),
    listTemplates: (...args: unknown[]) => mockListTemplates(...args),
    update: (...args: unknown[]) => mockUpdate(...args),
    inlineUpdate: (...args: unknown[]) => mockInlineUpdate(...args),
  },
  pipelinesApi: {
    list: (...args: unknown[]) => mockPipelinesList(...args),
  },
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public error: { error: string }
    ) {
      super(error.error);
    }
  },
}));

// ── Wrapper ──

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

// ── Factory ──

function createChore(overrides: Partial<Chore> = {}): Chore {
  return {
    id: 'chore-1',
    project_id: 'PVT_1',
    name: 'Bug Bash',
    template_path: '.github/ISSUE_TEMPLATE/bug-bash.md',
    template_content: '---\nname: Bug Bash\n---\nContent',
    schedule_type: 'time',
    schedule_value: 14,
    status: 'active',
    last_triggered_at: null,
    last_triggered_count: 0,
    current_issue_number: null,
    current_issue_node_id: null,
    pr_number: null,
    pr_url: null,
    tracking_issue_number: null,
    execution_count: 0,
    ai_enhance_enabled: true,
    agent_pipeline_id: '',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

// ── Tests ──

describe('ChoresPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListTemplates.mockResolvedValue([]);
    mockUpdate.mockResolvedValue(createChore());
    mockInlineUpdate.mockResolvedValue({
      chore: createChore(),
      pr_number: 101,
      pr_url: 'https://example.test/pr/101',
      pr_merged: false,
      merge_error: null,
    });
    mockPipelinesList.mockResolvedValue({
      pipelines: [{ id: 'pipe-1', name: 'Advanced Pipeline' }],
    });
  });

  it('renders empty state when no chores exist', async () => {
    mockList.mockResolvedValue([]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('No chores yet')).toBeInTheDocument();
    });

    expect(screen.getByText(/Create a chore to set up/)).toBeInTheDocument();
  });

  it('renders chore list with ChoreCards', async () => {
    mockList.mockResolvedValue([
      createChore({ id: 'c1', name: 'Bug Bash' }),
      createChore({
        id: 'c2',
        name: 'Dependency Update',
        schedule_type: 'count',
        schedule_value: 5,
      }),
    ]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getAllByText('Bug Bash').length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText('Dependency Update').length).toBeGreaterThan(0);
  });

  it('renders loading state with CelestialLoader', () => {
    // Never resolve the promise to keep loading state
    mockList.mockReturnValue(new Promise(() => {}));

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    // Should show the CelestialLoader spinner (role="status")
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders error state when API call fails', async () => {
    mockList.mockRejectedValue(new Error('Network error'));

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Could not load chores')).toBeInTheDocument();
    });
  });

  it('renders a rate limit message and retries when the chores query is throttled', async () => {
    const user = userEvent.setup();
    mockList
      .mockRejectedValueOnce(new ApiError(429, { error: 'Too many requests' }))
      .mockResolvedValueOnce([]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    expect(await screen.findByText('Rate limit reached')).toBeInTheDocument();
    expect(
      screen.getByText('Too many requests. Please wait a moment and try again.')
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Retry' }));

    await waitFor(() => {
      expect(mockList).toHaveBeenCalledTimes(2);
      expect(screen.getByText('No chores yet')).toBeInTheDocument();
    });
  });

  it('displays the Chores header', async () => {
    mockList.mockResolvedValue([]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Recurring work, given actual breathing room')).toBeInTheDocument();
    });
  });

  it('shows Active badge for active chores', async () => {
    mockList.mockResolvedValue([createChore({ status: 'active' })]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      const buttons = screen.getAllByRole('button', { name: 'Click to pause' });
      expect(buttons.length).toBeGreaterThan(0);
      buttons.forEach((button) => {
        expect(button).toHaveTextContent('Active');
      });
    });
  });

  it('shows Paused badge for paused chores', async () => {
    mockList.mockResolvedValue([createChore({ status: 'paused' })]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      const buttons = screen.getAllByRole('button', { name: 'Click to activate' });
      expect(buttons.length).toBeGreaterThan(0);
      buttons.forEach((button) => {
        expect(button).toHaveTextContent('Paused');
      });
    });
  });

  it('saves a selected saved pipeline from chore inline edit', async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([
      createChore({ id: 'c1', name: 'Bug Bash', agent_pipeline_id: '' }),
    ]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: 'Edit chore' }).length).toBeGreaterThan(0);
    });

    await user.click(screen.getAllByRole('button', { name: 'Edit chore' })[0]);

    const pipelineSelectors = await screen.findAllByLabelText('Agent Pipeline');
    await user.selectOptions(pipelineSelectors[0], 'pipe-1');

    const saveButtons = screen.getAllByRole('button', { name: 'Save' });
    await user.click(saveButtons[0]);

    await waitFor(() => {
      expect(mockInlineUpdate).toHaveBeenCalledWith('PVT_1', 'c1', {
        agent_pipeline_id: 'pipe-1',
      });
    });
  });

  it('updates the pipeline directly from the pipeline pill pop-out', async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([
      createChore({ id: 'c1', name: 'Bug Bash', agent_pipeline_id: '' }),
    ]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    const pipelinePills = await screen.findAllByRole('button', { name: 'Agent Pipeline' });
    await user.click(pipelinePills[0]);
    await user.click(await screen.findByRole('option', { name: 'Advanced Pipeline' }));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith('PVT_1', 'c1', {
        agent_pipeline_id: 'pipe-1',
      });
    });
  });

  it('opens the add-chore modal with a spotlighted repository template prefilled', async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([createChore({ id: 'c1', name: 'Existing chore' })]);
    mockListTemplates.mockResolvedValue([
      {
        name: 'Weekly triage',
        path: '.github/ISSUE_TEMPLATE/weekly-triage.md',
        content: '## Weekly triage\nReview open issues',
        about: 'Keep the backlog healthy each week.',
      },
    ]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    expect(await screen.findByText('Repo template')).toBeInTheDocument();

    await user.click(await screen.findByRole('button', { name: /Weekly triage/i }));

    await waitFor(() => {
      expect(screen.getByText('Add Chore')).toBeInTheDocument();
      expect(screen.getByLabelText('Name')).toHaveValue('Weekly triage');
      expect(screen.getByLabelText('Template Content')).toHaveValue(
        '## Weekly triage\nReview open issues'
      );
    });
  });

  it('shows the no-results state for filters and resets back to the full catalog', async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([
      createChore({ id: 'c1', name: 'Alpha upkeep' }),
      createChore({ id: 'c2', name: 'Beta cleanup', template_path: '.github/ISSUE_TEMPLATE/beta.md' }),
    ]);

    render(<ChoresPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    const searchInput = await screen.findByLabelText('Search chores by name or template path');
    await user.type(searchInput, 'zzz');

    await waitFor(() => {
      expect(screen.getByText('No chores match the current filters.')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Reset filters' }));

    await waitFor(() => {
      expect(screen.queryByText('No chores match the current filters.')).not.toBeInTheDocument();
      expect(screen.getAllByText('Alpha upkeep').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Beta cleanup').length).toBeGreaterThan(0);
      expect(searchInput).toHaveValue('');
    });
  });
});
