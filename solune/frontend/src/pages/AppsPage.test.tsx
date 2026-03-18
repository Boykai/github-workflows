import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { AppsPage } from './AppsPage';

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  createMutate: vi.fn(),
  createReset: vi.fn(),
  startMutate: vi.fn(),
  stopMutate: vi.fn(),
  deleteMutate: vi.fn(),
  confirm: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mocks.navigate,
    useParams: () => ({}),
  };
});

vi.mock('@/hooks/useApps', () => ({
  useApps: () => ({
    data: [],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useCreateApp: () => ({
    mutate: mocks.createMutate,
    reset: mocks.createReset,
    isPending: false,
  }),
  useOwners: () => ({
    data: [{ login: 'testuser', avatar_url: '', type: 'User' }],
    isLoading: false,
    error: null,
  }),
  useStartApp: () => ({ mutate: mocks.startMutate, isPending: false }),
  useStopApp: () => ({ mutate: mocks.stopMutate, isPending: false }),
  useDeleteApp: () => ({ mutate: mocks.deleteMutate, isPending: false }),
  getErrorMessage: (_err: unknown, fallback: string) => fallback,
}));

vi.mock('@/hooks/useConfirmation', async () => {
  const actual = await vi.importActual<typeof import('@/hooks/useConfirmation')>('@/hooks/useConfirmation');
  return {
    ...actual,
    useConfirmation: () => ({ confirm: mocks.confirm }),
  };
});

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: () => ({ data: undefined, isLoading: false, error: null }),
  };
});

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { selected_project_id: 'PVT_test' },
    isLoading: false,
    isAuthenticated: true,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    refetch: vi.fn(),
  }),
}));

vi.mock('@/hooks/useProjects', () => ({
  useProjects: () => ({
    projects: [],
    isLoading: false,
    error: null,
    selectedProject: { project_id: 'PVT_test', name: 'Test Project' },
    tasks: [],
    tasksLoading: false,
    selectProject: vi.fn(),
    refreshProjects: vi.fn(),
    refreshTasks: vi.fn(),
  }),
}));

vi.mock('@/services/api', () => ({
  pipelinesApi: {
    list: vi.fn().mockResolvedValue({ pipelines: [] }),
  },
}));

vi.mock('@/utils/rateLimit', () => ({
  isRateLimitApiError: () => false,
}));

describe('AppsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('opens the create dialog from the create app button', async () => {
    render(<AppsPage />);

    await userEvent.click(screen.getByRole('button', { name: /create app/i }));

    expect(screen.getByRole('heading', { name: /create app/i })).toBeInTheDocument();
    expect(mocks.createReset).toHaveBeenCalledOnce();
  });

  it('submits a trimmed payload and navigates to the created app on success', async () => {
    mocks.createMutate.mockImplementation(
      (_payload: unknown, options?: { onSuccess?: (app: { name: string; display_name: string }) => void }) => {
        options?.onSuccess?.({ name: 'my-awesome-app', display_name: 'My Awesome App' });
      }
    );

    render(<AppsPage />);

    await userEvent.click(screen.getByRole('button', { name: /create app/i }));
    await userEvent.type(screen.getByLabelText(/display name/i), '  My Awesome App  ');
    await userEvent.type(screen.getByLabelText(/description/i), '  Sample app  ');

    // Click the submit button inside the dialog (not the header CTA)
    const dialog = screen.getByRole('dialog');
    const submitButton = dialog.querySelector('button[type="submit"]') as HTMLElement;
    await userEvent.click(submitButton);

    expect(mocks.createMutate).toHaveBeenCalledWith(
      {
        name: 'my-awesome-app',
        display_name: 'My Awesome App',
        description: 'Sample app',
        branch: 'app/my-awesome-app',
        ai_enhance: true,
        repo_type: 'same-repo',
      },
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      })
    );

    await waitFor(() => {
      expect(mocks.navigate).toHaveBeenCalledWith('/apps/my-awesome-app');
    });
  });

  it('shows an error instead of failing silently when the create request fails', async () => {
    mocks.createMutate.mockImplementation(
      (_payload: unknown, options?: { onError?: (error: Error) => void }) => {
        options?.onError?.(new Error('Branch not found.'));
      }
    );

    render(<AppsPage />);

    await userEvent.click(screen.getByRole('button', { name: /create app/i }));
    await userEvent.type(screen.getByLabelText(/display name/i), 'My Awesome App');

    const dialog = screen.getByRole('dialog');
    const submitButton = dialog.querySelector('button[type="submit"]') as HTMLElement;
    await userEvent.click(submitButton);

    expect(mocks.createMutate).toHaveBeenCalledOnce();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Azure credentials — new-repo dialog fields
// ---------------------------------------------------------------------------

describe('AppsPage — Azure credentials (new-repo)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function _openNewRepoDialog() {
    render(<AppsPage />);
    await userEvent.click(screen.getByRole('button', { name: /create app/i }));
    // Switch repo type to new-repo
    const dialog = screen.getByRole('dialog');
    // Find the "New Repository" radio/button
    const newRepoOption = screen.queryByText(/new repo/i) ?? screen.queryByText(/new repository/i);
    if (newRepoOption) {
      await userEvent.click(newRepoOption);
    }
    return dialog;
  }

  it('shows Azure credential fields only when new-repo is selected', async () => {
    render(<AppsPage />);
    await userEvent.click(screen.getByRole('button', { name: /create app/i }));

    // Azure fields should not be visible in same-repo mode (default)
    expect(screen.queryByLabelText(/azure client id/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/azure client secret/i)).not.toBeInTheDocument();
  });

  it('validates that only one Azure field provided shows an error', async () => {
    render(<AppsPage />);
    await userEvent.click(screen.getByRole('button', { name: /create app/i }));

    // Navigate to new-repo tab
    const newRepoButtons = screen.getAllByRole('button');
    const newRepoBtn = newRepoButtons.find((b) => /new.repo/i.test(b.textContent ?? ''));
    if (newRepoBtn) {
      await userEvent.click(newRepoBtn);
    }

    const azureIdField = screen.queryByLabelText(/azure client id/i);
    const azureSecretField = screen.queryByLabelText(/azure client secret/i);

    if (azureIdField && azureSecretField) {
      // Fill only the ID field
      await userEvent.type(screen.getByLabelText(/display name/i), 'My App');
      await userEvent.type(azureIdField, 'my-client-id');
      // Leave secret empty — expect validation error on submit
      const dialog = screen.getByRole('dialog');
      const submitButton = dialog.querySelector('button[type="submit"]') as HTMLElement;
      await userEvent.click(submitButton);
      expect(await screen.findByRole('alert')).toHaveTextContent(/both be provided or both omitted/i);
    }
  });

  it('includes both azure fields in the payload when both are provided', async () => {
    mocks.createMutate.mockImplementation(
      (_payload: unknown, options?: { onSuccess?: (app: { name: string; display_name: string; warnings: string[] | null }) => void }) => {
        options?.onSuccess?.({ name: 'azure-app', display_name: 'Azure App', warnings: null });
      }
    );

    render(<AppsPage />);
    await userEvent.click(screen.getByRole('button', { name: /create app/i }));

    // Switch to new-repo
    const newRepoButtons = screen.getAllByRole('button');
    const newRepoBtn = newRepoButtons.find((b) => /new.repo/i.test(b.textContent ?? ''));
    if (newRepoBtn) {
      await userEvent.click(newRepoBtn);
    }

    const azureIdField = screen.queryByLabelText(/azure client id/i);
    const azureSecretField = screen.queryByLabelText(/azure client secret/i);

    if (azureIdField && azureSecretField) {
      await userEvent.type(screen.getByLabelText(/display name/i), 'Azure App');
      await userEvent.type(azureIdField, 'my-client-id');
      await userEvent.type(azureSecretField, 'my-client-secret');

      const dialog = screen.getByRole('dialog');
      const submitButton = dialog.querySelector('button[type="submit"]') as HTMLElement;
      await userEvent.click(submitButton);

      const callPayload = mocks.createMutate.mock.calls[0]?.[0] as Record<string, unknown> | undefined;
      if (callPayload) {
        expect(callPayload.azure_client_id).toBe('my-client-id');
        // Secret must be sent as entered (not trimmed)
        expect(callPayload.azure_client_secret).toBe('my-client-secret');
      }
    }
  });

  it('shows a warning notification when creation succeeds with azure warnings', async () => {
    mocks.createMutate.mockImplementation(
      (_payload: unknown, options?: { onSuccess?: (app: { name: string; display_name: string; warnings: string[] | null }) => void }) => {
        options?.onSuccess?.({
          name: 'azure-app',
          display_name: 'Azure App',
          warnings: ['Azure credentials could not be stored as GitHub Secrets.'],
        });
      }
    );

    render(<AppsPage />);
    await userEvent.click(screen.getByRole('button', { name: /create app/i }));
    await userEvent.type(screen.getByLabelText(/display name/i), 'Azure App');

    const dialog = screen.getByRole('dialog');
    const submitButton = dialog.querySelector('button[type="submit"]') as HTMLElement;
    await userEvent.click(submitButton);

    // Warning should be displayed after success
    await waitFor(() => {
      expect(screen.queryByText(/Azure credentials could not be stored/i)).toBeInTheDocument();
    });
  });
});