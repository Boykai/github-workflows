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
  }),
  useCreateApp: () => ({
    mutate: mocks.createMutate,
    reset: mocks.createReset,
    isPending: false,
  }),
  useStartApp: () => ({ mutate: mocks.startMutate }),
  useStopApp: () => ({ mutate: mocks.stopMutate }),
  useDeleteApp: () => ({ mutate: mocks.deleteMutate }),
}));

describe('AppsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('opens the create dialog from the new app button', async () => {
    render(<AppsPage />);

    await userEvent.click(screen.getByRole('button', { name: /new app/i }));

    expect(screen.getByRole('heading', { name: /create new app/i })).toBeInTheDocument();
    expect(mocks.createReset).toHaveBeenCalledOnce();
  });

  it('submits a trimmed payload and navigates to the created app on success', async () => {
    mocks.createMutate.mockImplementation(
      (_payload: unknown, options?: { onSuccess?: (app: { name: string }) => void }) => {
        options?.onSuccess?.({ name: 'my-awesome-app' });
      }
    );

    render(<AppsPage />);

    await userEvent.click(screen.getByRole('button', { name: /new app/i }));
  await userEvent.type(screen.getByLabelText(/^name$/i), 'my-awesome-app');
    await userEvent.type(screen.getByLabelText(/display name/i), '  My Awesome App  ');
    await userEvent.type(screen.getByLabelText(/description/i), '  Sample app  ');
    await userEvent.type(screen.getByLabelText(/target branch/i), '  feature/my-app  ');

    await userEvent.click(screen.getByRole('button', { name: /create app/i }));

    expect(mocks.createMutate).toHaveBeenCalledWith(
      {
        name: 'my-awesome-app',
        display_name: 'My Awesome App',
        description: 'Sample app',
        branch: 'feature/my-app',
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

    await userEvent.click(screen.getByRole('button', { name: /new app/i }));
    await userEvent.type(screen.getByLabelText(/^name$/i), 'my-awesome-app');
    await userEvent.type(screen.getByLabelText(/display name/i), 'My Awesome App');
    await userEvent.type(screen.getByLabelText(/target branch/i), 'missing-branch');
    await userEvent.click(screen.getByRole('button', { name: /create app/i }));

    expect(mocks.createMutate).toHaveBeenCalledOnce();
    expect(await screen.findByRole('alert')).toHaveTextContent('Branch not found.');
  });
});