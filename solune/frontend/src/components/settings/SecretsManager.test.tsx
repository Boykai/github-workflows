/**
 * Tests for SecretsManager component.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, userEvent, waitFor, fireEvent } from '@/test/test-utils';
import { SecretsManager } from './SecretsManager';
import type { Project } from '@/types';

// ── Hoisted mocks ──

const mocks = vi.hoisted(() => ({
  setSecretMutateAsync: vi.fn().mockResolvedValue(undefined),
  deleteSecretMutateAsync: vi.fn().mockResolvedValue(undefined),
  secretsData: undefined as { secrets: Array<{ name: string; created_at: string; updated_at: string }>; total_count: number } | undefined,
  secretsLoading: false,
  setSecretIsPending: false,
  deleteSecretIsPending: false,
}));

vi.mock('@/hooks/useSecrets', () => ({
  useSecrets: () => ({
    data: mocks.secretsData,
    isLoading: mocks.secretsLoading,
  }),
  useSetSecret: () => ({
    mutateAsync: mocks.setSecretMutateAsync,
    isPending: mocks.setSecretIsPending,
  }),
  useDeleteSecret: () => ({
    mutateAsync: mocks.deleteSecretMutateAsync,
    isPending: mocks.deleteSecretIsPending,
  }),
}));

// ── Test fixtures ──

const mockProjects: Project[] = [
  {
    project_id: 'PVT_1',
    name: 'my-repo',
    owner_login: 'owner1',
    project_number: 1,
    status_field_id: 'sf1',
    columns: [],
  },
  {
    project_id: 'PVT_2',
    name: 'another-repo',
    owner_login: 'owner2',
    project_number: 2,
    status_field_id: 'sf2',
    columns: [],
  },
];

describe('SecretsManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.secretsData = undefined;
    mocks.secretsLoading = false;
    mocks.setSecretIsPending = false;
    mocks.deleteSecretIsPending = false;
  });

  it('shows empty state when no projects are provided', () => {
    render(<SecretsManager projects={[]} />);
    expect(screen.getByText(/No repositories available/)).toBeInTheDocument();
  });

  it('renders repository selector with project options', () => {
    render(<SecretsManager projects={mockProjects} />);
    expect(screen.getByLabelText('Repository')).toBeInTheDocument();
    expect(screen.getByText('Select a repository…')).toBeInTheDocument();
  });

  it('shows environment name after selecting a repo', async () => {
    render(<SecretsManager projects={mockProjects} />);
    const select = screen.getByLabelText('Repository');
    await userEvent.setup().selectOptions(select, 'owner1/my-repo');

    expect(screen.getByText('copilot')).toBeInTheDocument();
  });

  it('shows known secrets section after selecting a repo', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const select = screen.getByLabelText('Repository');
    await userEvent.setup().selectOptions(select, 'owner1/my-repo');

    expect(screen.getByText('Known Secrets')).toBeInTheDocument();
    expect(screen.getByText('Context7 API Key')).toBeInTheDocument();
    expect(screen.getByText('Not Set')).toBeInTheDocument();
  });

  it('shows Set button for known secret that is not set', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    await userEvent.setup().selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');

    expect(screen.getByRole('button', { name: 'Set' })).toBeInTheDocument();
  });

  it('shows Update and Remove buttons for known secret that is set', async () => {
    mocks.secretsData = {
      secrets: [
        { name: 'COPILOT_MCP_CONTEXT7_API_KEY', created_at: '2024-01-01', updated_at: '2024-01-01' },
      ],
      total_count: 1,
    };

    render(<SecretsManager projects={mockProjects} />);
    await userEvent.setup().selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');

    expect(screen.getByText('✓ Set')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Update' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove' })).toBeInTheDocument();
  });

  it('opens editing form when Set button is clicked', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');
    await user.click(screen.getByRole('button', { name: 'Set' }));

    expect(screen.getByLabelText('Secret value for Context7 API Key')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('calls setSecret mutation when saving a known secret', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');
    await user.click(screen.getByRole('button', { name: 'Set' }));

    const input = screen.getByLabelText('Secret value for Context7 API Key');
    await user.type(input, 'my-secret-value');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(mocks.setSecretMutateAsync).toHaveBeenCalledWith({
        owner: 'owner1',
        repo: 'my-repo',
        env: 'copilot',
        name: 'COPILOT_MCP_CONTEXT7_API_KEY',
        value: 'my-secret-value',
      });
    });
  });

  it('calls deleteSecret mutation when removing a known secret', async () => {
    mocks.secretsData = {
      secrets: [
        { name: 'COPILOT_MCP_CONTEXT7_API_KEY', created_at: '2024-01-01', updated_at: '2024-01-01' },
      ],
      total_count: 1,
    };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');
    await user.click(screen.getByRole('button', { name: 'Remove' }));

    await waitFor(() => {
      expect(mocks.deleteSecretMutateAsync).toHaveBeenCalledWith({
        owner: 'owner1',
        repo: 'my-repo',
        env: 'copilot',
        name: 'COPILOT_MCP_CONTEXT7_API_KEY',
      });
    });
  });

  it('shows show/hide toggle for secret value input', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');
    await user.click(screen.getByRole('button', { name: 'Set' }));

    const input = screen.getByLabelText('Secret value for Context7 API Key');
    expect(input).toHaveAttribute('type', 'password');

    await user.click(screen.getByRole('button', { name: 'Show value' }));
    expect(input).toHaveAttribute('type', 'text');

    await user.click(screen.getByRole('button', { name: 'Hide value' }));
    expect(input).toHaveAttribute('type', 'password');
  });

  it('cancels editing and clears form', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');
    await user.click(screen.getByRole('button', { name: 'Set' }));
    expect(screen.getByLabelText('Secret value for Context7 API Key')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByLabelText('Secret value for Context7 API Key')).not.toBeInTheDocument();
  });

  // Custom secrets section
  it('shows custom secrets form after selecting a repo', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    await userEvent.setup().selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');

    expect(screen.getByText('Custom Secrets')).toBeInTheDocument();
    expect(screen.getByLabelText('Custom secret name')).toBeInTheDocument();
    expect(screen.getByLabelText('Custom secret value')).toBeInTheDocument();
  });

  it('converts custom name to uppercase', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');
    await user.type(screen.getByLabelText('Custom secret name'), 'my_key');

    expect(screen.getByLabelText('Custom secret name')).toHaveValue('MY_KEY');
  });

  it('does not show prefix warning for COPILOT_MCP_ name', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');

    // When no name is entered, no warning should be shown
    expect(screen.queryByText(/COPILOT_MCP_ prefix/)).not.toBeInTheDocument();
  });

  it('validates custom secret name format', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');

    // Button should be disabled when name is empty
    expect(screen.getByRole('button', { name: 'Add Custom Secret' })).toBeDisabled();

    // Type value but leave name empty — button stays disabled
    await user.type(screen.getByLabelText('Custom secret value'), 'value');
    expect(screen.getByRole('button', { name: 'Add Custom Secret' })).toBeDisabled();
  });

  it('validates custom secret requires value', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');

    // Type name but leave value empty — button stays disabled
    await user.type(screen.getByLabelText('Custom secret name'), 'COPILOT_MCP_MY_KEY');
    expect(screen.getByRole('button', { name: 'Add Custom Secret' })).toBeDisabled();
  });

  it('calls setSecret for custom secret and clears form', async () => {
    mocks.secretsData = { secrets: [], total_count: 0 };

    render(<SecretsManager projects={mockProjects} />);
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');
    await user.type(screen.getByLabelText('Custom secret name'), 'COPILOT_MCP_MY_KEY');
    await user.type(screen.getByLabelText('Custom secret value'), 'my-value');
    await user.click(screen.getByRole('button', { name: 'Add Custom Secret' }));

    await waitFor(() => {
      expect(mocks.setSecretMutateAsync).toHaveBeenCalledWith({
        owner: 'owner1',
        repo: 'my-repo',
        env: 'copilot',
        name: 'COPILOT_MCP_MY_KEY',
        value: 'my-value',
      });
    });
  });

  it('shows loading state while fetching secrets', async () => {
    mocks.secretsLoading = true;

    render(<SecretsManager projects={mockProjects} />);
    await userEvent.setup().selectOptions(screen.getByLabelText('Repository'), 'owner1/my-repo');

    expect(screen.getByText('Loading secrets…')).toBeInTheDocument();
  });

  it('deduplicates repos from projects', () => {
    const duplicateProjects: Project[] = [
      { ...mockProjects[0] },
      { ...mockProjects[0], project_id: 'PVT_3' }, // same owner/repo, different project_id
    ];

    render(<SecretsManager projects={duplicateProjects} />);
    const options = screen.getAllByRole('option');
    // 1 placeholder + 1 unique repo (not 2)
    expect(options).toHaveLength(2);
  });
});
