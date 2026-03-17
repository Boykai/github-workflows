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

vi.mock('@/hooks/useConfirmation', () => ({
  useConfirmation: () => ({ confirm: mocks.confirm }),
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