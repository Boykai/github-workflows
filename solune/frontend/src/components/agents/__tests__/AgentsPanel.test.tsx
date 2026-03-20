import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import { within } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { AgentsPanel } from '../AgentsPanel';
import type { AgentConfig } from '@/services/api';

const mockUseAgentsList = vi.fn();
const mockUseAgentsListPaginated = vi.fn();
const mockUsePendingAgentsList = vi.fn();
const mockUseClearPendingAgents = vi.fn();
const mockUseDeleteAgent = vi.fn();
const mockUseUndoableDeleteAgent = vi.fn();
const mockUseCreateAgent = vi.fn();
const mockUseUpdateAgent = vi.fn();
const mockUseBulkUpdateModels = vi.fn();
const mockUseModels = vi.fn();
const mockUseUnsavedChanges = vi.fn();

vi.mock('@/hooks/useModels', () => ({
  useModels: (...args: unknown[]) => mockUseModels(...args),
}));

vi.mock('@/components/pipeline/ModelSelector', () => ({
  ModelSelector: ({ onSelect }: { onSelect?: (id: string, name: string) => void }) => (
    <button type="button" onClick={() => onSelect?.('model-1', 'GPT-5')}>
      Select model
    </button>
  ),
}));

vi.mock('@/hooks/useAgents', () => ({
  useAgentsList: (...args: unknown[]) => mockUseAgentsList(...args),
  useAgentsListPaginated: (...args: unknown[]) => mockUseAgentsListPaginated(...args),
  usePendingAgentsList: (...args: unknown[]) => mockUsePendingAgentsList(...args),
  useClearPendingAgents: (...args: unknown[]) => mockUseClearPendingAgents(...args),
  useDeleteAgent: (...args: unknown[]) => mockUseDeleteAgent(...args),
  useUndoableDeleteAgent: (...args: unknown[]) => mockUseUndoableDeleteAgent(...args),
  useCreateAgent: (...args: unknown[]) => mockUseCreateAgent(...args),
  useUpdateAgent: (...args: unknown[]) => mockUseUpdateAgent(...args),
  useBulkUpdateModels: (...args: unknown[]) => mockUseBulkUpdateModels(...args),
}));

vi.mock('@/hooks/useUnsavedChanges', () => ({
  useUnsavedChanges: (...args: unknown[]) => mockUseUnsavedChanges(...args),
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

function createAgent(overrides: Partial<AgentConfig> = {}): AgentConfig {
  return {
    id: 'agent-1',
    name: 'Reviewer',
    slug: 'reviewer',
    description: 'Reviews pull requests',
    system_prompt: 'Review carefully',
    status: 'pending_pr',
    tools: ['read', 'comment'],
    status_column: null,
    github_issue_number: null,
    github_pr_number: 44,
    branch_name: 'agent/reviewer',
    source: 'local',
    created_at: '2026-03-01T00:00:00Z',
    ...overrides,
  };
}

describe('AgentsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAgentsList.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({
      allItems: [],
      isLoading: false,
      isError: false,
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage: vi.fn(),
      invalidate: vi.fn(),
    });
    mockUsePendingAgentsList.mockReturnValue({
      data: [],
      isLoading: false,
    });
    mockUseClearPendingAgents.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
      data: undefined,
      error: null,
    });
    mockUseDeleteAgent.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
      data: undefined,
      error: null,
    });
    mockUseUndoableDeleteAgent.mockReturnValue({
      deleteAgent: vi.fn(),
      pendingIds: new Set<string>(),
    });
    mockUseCreateAgent.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    mockUseUpdateAgent.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({ pr_url: 'https://example.test/pr/1' }),
      isPending: false,
    });
    mockUseBulkUpdateModels.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
      data: undefined,
      error: null,
    });
    mockUseModels.mockReturnValue({
      refreshModels: vi.fn(),
      isRefreshing: false,
    });
    mockUseUnsavedChanges.mockReturnValue({
      blocker: { state: 'unblocked', proceed: vi.fn(), reset: vi.fn() },
      isBlocked: false,
    });
  });

  it('prioritizes the top three used agents in the featured section', () => {
    const agents = [
      createAgent({ id: 'a1', slug: 'alpha', name: 'Alpha', created_at: '2026-03-01T00:00:00Z' }),
      createAgent({ id: 'a2', slug: 'beta', name: 'Beta', created_at: '2026-03-01T00:00:00Z' }),
      createAgent({ id: 'a3', slug: 'gamma', name: 'Gamma', created_at: '2026-03-01T00:00:00Z' }),
      createAgent({ id: 'a4', slug: 'delta', name: 'Delta', created_at: '2026-03-01T00:00:00Z' }),
    ];
    mockUseAgentsList.mockReturnValue({ data: agents, isLoading: false, error: null });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: agents, isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });

    render(
      <AgentsPanel
        projectId="PVT_1"
        agentUsageCounts={{ alpha: 7, beta: 5, gamma: 3, delta: 1 }}
      />,
      { wrapper: createWrapper() }
    );

    const featuredHeading = screen.getByRole('heading', {
      name: 'The agents setting the tone right now',
    });
    const featuredSection = featuredHeading.closest('section');
    expect(featuredSection).not.toBeNull();

    const featured = within(featuredSection as HTMLElement);
    expect(featured.getByText('Alpha')).toBeInTheDocument();
    expect(featured.getByText('Beta')).toBeInTheDocument();
    expect(featured.getByText('Gamma')).toBeInTheDocument();
    expect(featured.queryByText('Delta')).not.toBeInTheDocument();
  });

  it('supplements featured agents with recent agents when usage data has fewer than three matches', () => {
    const now = new Date().toISOString();
    const agents = [
      createAgent({ id: 'a1', slug: 'alpha', name: 'Alpha', created_at: '2026-03-01T00:00:00Z' }),
      createAgent({ id: 'a2', slug: 'beta', name: 'Beta', created_at: now }),
      createAgent({ id: 'a3', slug: 'gamma', name: 'Gamma', created_at: now }),
      createAgent({ id: 'a4', slug: 'delta', name: 'Delta', created_at: '2026-02-01T00:00:00Z' }),
    ];
    mockUseAgentsList.mockReturnValue({ data: agents, isLoading: false, error: null });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: agents, isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });

    render(
      <AgentsPanel
        projectId="PVT_1"
        agentUsageCounts={{ alpha: 4, beta: 0, gamma: 0, delta: 0 }}
      />,
      { wrapper: createWrapper() }
    );

    const featuredHeading = screen.getByRole('heading', {
      name: 'The agents setting the tone right now',
    });
    const featured = within(featuredHeading.closest('section') as HTMLElement);
    expect(featured.getByText('Alpha')).toBeInTheDocument();
    expect(featured.getByText('Beta')).toBeInTheDocument();
    expect(featured.getByText('Gamma')).toBeInTheDocument();
    expect(featured.queryByText('Delta')).not.toBeInTheDocument();
  });

  it('opens the bulk model update dialog from the catalog controls', async () => {
    mockUseAgentsList.mockReturnValue({
      data: [createAgent({ id: 'a1', slug: 'alpha', name: 'Alpha' })],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: [createAgent({ id: 'a1', slug: 'alpha', name: 'Alpha' })], isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });
    mockUsePendingAgentsList.mockReturnValue({
      data: [createAgent({ id: 'p1', slug: 'beta', name: 'Beta', status: 'pending_pr' })],
      isLoading: false,
    });

    render(<AgentsPanel projectId="PVT_1" />, { wrapper: createWrapper() });
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /update all models/i }));

    expect(screen.getByRole('dialog', { name: 'Bulk model update dialog' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Update All Agent Models' })).toBeInTheDocument();
    expect(
      screen.getByText(/Select the target model to apply to all 2 agents/i)
    ).toBeInTheDocument();
  });

  it('opens the inline editor for pending local agents', async () => {
    mockUsePendingAgentsList.mockReturnValue({
      data: [createAgent()],
      isLoading: false,
    });

    render(<AgentsPanel projectId="PVT_1" />, { wrapper: createWrapper() });
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByText('Pending changes')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Edit' }));

    await waitFor(() => {
      expect(screen.getByText('Editing agent definition')).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue('Reviewer')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Review carefully')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument();
  });

  it('allows editing repository agents so tools can be updated', async () => {
    mockUseAgentsList.mockReturnValue({
      data: [createAgent({ id: 'repo:reviewer', source: 'repo', status: 'active' })],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: [createAgent({ id: 'repo:reviewer', source: 'repo', status: 'active' })], isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });

    render(<AgentsPanel projectId="PVT_1" />, { wrapper: createWrapper() });
    const user = userEvent.setup();

    await user.click(screen.getAllByRole('button', { name: 'Edit' })[0]);

    await waitFor(() => {
      expect(screen.getByText('Editing agent definition')).toBeInTheDocument();
    });

    expect(screen.getByText('MCP Tools')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add Tools' })).toBeInTheDocument();
  });

  it('renders pretty names for spec kit agents in the catalog', () => {
    mockUseAgentsList.mockReturnValue({
      data: [
        createAgent({
          id: 'repo:speckit-clarify',
          name: 'Speckit.Clarify',
          slug: 'speckit.clarify',
          source: 'repo',
          status: 'active',
        }),
      ],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: [ createAgent({ id: 'repo:speckit-clarify', name: 'Speckit.Clarify', slug: 'speckit.clarify', source: 'repo', status: 'active', }), ], isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });

    render(<AgentsPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    expect(screen.getByText('Clarify (Spec Kit)')).toBeInTheDocument();
    expect(screen.queryByText('Speckit.Clarify')).not.toBeInTheDocument();
  });

  it('shows recently added for new agents and pending sub-issue counts from cached board data', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-08T12:00:00Z'));

    mockUseAgentsList.mockReturnValue({
      data: [
        createAgent({
          id: 'repo:alpha',
          slug: 'alpha',
          name: 'Alpha',
          source: 'repo',
          status: 'active',
          created_at: '2026-03-07T08:00:00Z',
        }),
      ],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: [ createAgent({ id: 'repo:alpha', slug: 'alpha', name: 'Alpha', source: 'repo', status: 'active', created_at: '2026-03-07T08:00:00Z', }), ], isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });

    render(<AgentsPanel projectId="PVT_1" pendingSubIssueCounts={{ alpha: 3 }} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getAllByText('Recently added').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Assigned sub-issues').length).toBeGreaterThan(0);
    expect(screen.getAllByText('3 open').length).toBeGreaterThan(0);

    vi.useRealTimers();
  });

  it('shows config pill counts from saved pipeline usage', () => {
    mockUseAgentsList.mockReturnValue({
      data: [
        createAgent({
          id: 'repo:alpha',
          slug: 'alpha',
          name: 'Alpha',
          source: 'repo',
          status: 'active',
        }),
      ],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: [ createAgent({ id: 'repo:alpha', slug: 'alpha', name: 'Alpha', source: 'repo', status: 'active', }), ], isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });

    render(
      <AgentsPanel
        projectId="PVT_1"
        agentUsageCounts={{ alpha: 9 }}
        pipelineConfigCounts={{ alpha: 2 }}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getAllByText('2 configs').length).toBeGreaterThan(0);
    expect(screen.queryByText('9 configs')).not.toBeInTheDocument();
  });

  it('shows the creation timestamp after the recent window expires', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-08T12:00:00Z'));

    const createdAt = '2026-03-04T08:00:00Z';
    const expected = new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(Date.parse(createdAt));

    mockUseAgentsList.mockReturnValue({
      data: [
        createAgent({
          id: 'repo:alpha',
          slug: 'alpha',
          name: 'Alpha',
          source: 'repo',
          status: 'active',
          created_at: createdAt,
        }),
      ],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: [ createAgent({ id: 'repo:alpha', slug: 'alpha', name: 'Alpha', source: 'repo', status: 'active', created_at: createdAt, }), ], isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });

    render(<AgentsPanel projectId="PVT_1" />, { wrapper: createWrapper() });

    expect(screen.getByText(expected)).toBeInTheDocument();

    vi.useRealTimers();
  });

  it('saves inline edits and surfaces the PR link', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({ pr_url: 'https://example.test/pr/99' });
    mockUseAgentsList.mockReturnValue({
      data: [createAgent({ status: 'active', source: 'both' })],
      isLoading: false,
      error: null,
    });
    mockUseAgentsListPaginated.mockReturnValue({ allItems: [createAgent({ status: 'active', source: 'both' })], isLoading: false, isError: false, hasNextPage: false, isFetchingNextPage: false, fetchNextPage: vi.fn(), invalidate: vi.fn() });
    mockUseUpdateAgent.mockReturnValue({
      mutateAsync,
      isPending: false,
    });

    render(<AgentsPanel projectId="PVT_1" />, { wrapper: createWrapper() });
    const user = userEvent.setup();

    await user.click(screen.getAllByRole('button', { name: 'Edit' })[0]);
    await user.clear(screen.getByLabelText('Name'));
    await user.type(screen.getByLabelText('Name'), 'Reviewer Updated');
    await user.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        agentId: 'agent-1',
        data: {
          name: 'Reviewer Updated',
          system_prompt: 'Review carefully',
          tools: ['read', 'comment'],
        },
      });
    });

    expect(await screen.findByRole('link', { name: 'View Pull Request' })).toHaveAttribute(
      'href',
      'https://example.test/pr/99'
    );
  });
});
