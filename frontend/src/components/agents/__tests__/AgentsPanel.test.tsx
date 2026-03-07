import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { AgentsPanel } from '../AgentsPanel';
import type { AgentConfig } from '@/services/api';

const mockUseAgentsList = vi.fn();
const mockUsePendingAgentsList = vi.fn();
const mockUseClearPendingAgents = vi.fn();
const mockUseDeleteAgent = vi.fn();
const mockUseCreateAgent = vi.fn();
const mockUseUpdateAgent = vi.fn();
const mockUseBulkUpdateModels = vi.fn();

vi.mock('@/hooks/useAgents', () => ({
  useAgentsList: (...args: unknown[]) => mockUseAgentsList(...args),
  usePendingAgentsList: (...args: unknown[]) => mockUsePendingAgentsList(...args),
  useClearPendingAgents: (...args: unknown[]) => mockUseClearPendingAgents(...args),
  useDeleteAgent: (...args: unknown[]) => mockUseDeleteAgent(...args),
  useCreateAgent: (...args: unknown[]) => mockUseCreateAgent(...args),
  useUpdateAgent: (...args: unknown[]) => mockUseUpdateAgent(...args),
  useBulkUpdateModels: (...args: unknown[]) => mockUseBulkUpdateModels(...args),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
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
  });

  it('opens the edit modal for pending local agents', async () => {
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
      expect(screen.getByRole('heading', { name: 'Edit Agent' })).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue('Reviewer')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Review carefully')).toBeInTheDocument();
  });
});
