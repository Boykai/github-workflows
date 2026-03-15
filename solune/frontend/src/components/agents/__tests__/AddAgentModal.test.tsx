import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/test/test-utils';

import { AddAgentModal } from '../AddAgentModal';
import type { AgentConfig } from '@/services/api';

const mockUseCreateAgent = vi.fn();
const mockUseUpdateAgent = vi.fn();
const mockUseToolsList = vi.fn();

vi.mock('@/hooks/useAgents', () => ({
  useCreateAgent: (...args: unknown[]) => mockUseCreateAgent(...args),
  useUpdateAgent: (...args: unknown[]) => mockUseUpdateAgent(...args),
}));

vi.mock('@/hooks/useTools', () => ({
  useToolsList: (...args: unknown[]) => mockUseToolsList(...args),
}));

function createAgent(overrides: Partial<AgentConfig> = {}): AgentConfig {
  return {
    id: 'agent-1',
    name: 'Reviewer',
    slug: 'reviewer',
    description: 'Reviews pull requests',
    system_prompt: 'Review carefully',
    default_model_id: '',
    default_model_name: '',
    status: 'pending_pr',
    tools: ['read'],
    status_column: null,
    github_issue_number: null,
    github_pr_number: 44,
    branch_name: 'agent/reviewer',
    source: 'local',
    created_at: '2026-03-01T00:00:00Z',
    ...overrides,
  };
}

describe('AddAgentModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseCreateAgent.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    mockUseUpdateAgent.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({
        pr_url: 'https://example.test/pr/1',
        pr_number: 1,
        issue_number: null,
        branch_name: 'branch',
        agent: createAgent(),
      }),
      isPending: false,
    });
    mockUseToolsList.mockReturnValue({ tools: [] });
  });

  it('saves from the unsaved-changes dialog without relying on the unmounted form element', async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      pr_url: 'https://example.test/pr/1',
      pr_number: 1,
      issue_number: null,
      branch_name: 'branch',
      agent: createAgent({ name: 'Reviewer Updated' }),
    });
    mockUseUpdateAgent.mockReturnValue({ mutateAsync, isPending: false });

    render(
      <AddAgentModal projectId="PVT_1" isOpen={true} onClose={vi.fn()} editAgent={createAgent()} />
    );

    await user.clear(screen.getByLabelText('Name'));
    await user.type(screen.getByLabelText('Name'), 'Reviewer Updated');
    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(screen.getByRole('dialog', { name: /unsaved changes/i })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        agentId: 'agent-1',
        data: {
          name: 'Reviewer Updated',
          system_prompt: 'Review carefully',
          tools: ['read'],
        },
      });
    });

    expect(await screen.findByText('Agent Updated')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /view pull request/i })).toHaveAttribute(
      'href',
      'https://example.test/pr/1'
    );
  });
});
