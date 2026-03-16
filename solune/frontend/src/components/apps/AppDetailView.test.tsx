/**
 * Tests for AppDetailView component.
 * Covers: loading state, error/not-found state, rate-limit error, metadata display,
 * action buttons, confirmation dialogs, retry, mutation error feedback.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { AppDetailView } from './AppDetailView';
import type { App } from '@/types/apps';

const mocks = vi.hoisted(() => ({
  appData: null as App | null,
  isLoading: false,
  error: null as Error | null,
  refetch: vi.fn(),
  startMutate: vi.fn(),
  stopMutate: vi.fn(),
  deleteMutate: vi.fn(),
  startPending: false,
  stopPending: false,
  deletePending: false,
  startError: null as Error | null,
  stopError: null as Error | null,
  deleteError: null as Error | null,
  confirm: vi.fn().mockResolvedValue(true),
}));

vi.mock('@/hooks/useApps', () => ({
  useApp: () => ({
    data: mocks.appData,
    isLoading: mocks.isLoading,
    error: mocks.error,
    refetch: mocks.refetch,
  }),
  useStartApp: () => ({
    mutate: mocks.startMutate,
    isPending: mocks.startPending,
    error: mocks.startError,
  }),
  useStopApp: () => ({
    mutate: mocks.stopMutate,
    isPending: mocks.stopPending,
    error: mocks.stopError,
  }),
  useDeleteApp: () => ({
    mutate: mocks.deleteMutate,
    isPending: mocks.deletePending,
    error: mocks.deleteError,
  }),
  friendlyErrorMessage: (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback,
}));

vi.mock('@/hooks/useConfirmation', () => ({
  useConfirmation: () => ({ confirm: mocks.confirm }),
  ConfirmationDialogProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock('@/utils/rateLimit', () => ({
  isRateLimitApiError: (error: unknown) =>
    error instanceof Error && error.message.includes('rate limit'),
}));

function makeApp(overrides: Partial<App> = {}): App {
  return {
    name: 'test-app',
    display_name: 'Test App',
    description: 'A test application',
    directory_path: '/apps/test-app',
    associated_pipeline_id: null,
    status: 'stopped',
    repo_type: 'same-repo',
    external_repo_url: null,
    port: null,
    error_message: null,
    created_at: '2026-03-15T10:00:00Z',
    updated_at: '2026-03-15T12:00:00Z',
    ...overrides,
  };
}

describe('AppDetailView', () => {
  const onBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mocks.appData = null;
    mocks.isLoading = false;
    mocks.error = null;
    mocks.startPending = false;
    mocks.stopPending = false;
    mocks.deletePending = false;
    mocks.startError = null;
    mocks.stopError = null;
    mocks.deleteError = null;
  });

  it('shows loading state with CelestialLoader', () => {
    mocks.isLoading = true;

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows error state with retry button', () => {
    mocks.error = new Error('Server error');

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByText(/could not load app details/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('calls refetch when retry button is clicked', async () => {
    mocks.error = new Error('Server error');

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /retry/i }));

    expect(mocks.refetch).toHaveBeenCalledOnce();
  });

  it('shows rate limit message for rate limit errors', () => {
    mocks.error = new Error('rate limit exceeded');

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByText(/rate limit exceeded/i)).toBeInTheDocument();
  });

  it('renders app metadata when loaded', () => {
    mocks.appData = makeApp({ status: 'active', port: 3000 });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByText('Test App')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('3000')).toBeInTheDocument();
    expect(screen.getByText('same-repo')).toBeInTheDocument();
  });

  it('renders a time element for the created date', () => {
    mocks.appData = makeApp();

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(document.querySelector('time')).toBeInTheDocument();
  });

  it('shows Start button for stopped apps', () => {
    mocks.appData = makeApp({ status: 'stopped' });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByRole('button', { name: /start app/i })).toBeInTheDocument();
  });

  it('shows Stop button for active apps', () => {
    mocks.appData = makeApp({ status: 'active' });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByRole('button', { name: /stop app/i })).toBeInTheDocument();
  });

  it('shows Delete button for non-active apps', () => {
    mocks.appData = makeApp({ status: 'stopped' });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByRole('button', { name: /delete app/i })).toBeInTheDocument();
  });

  it('calls start mutation directly (no confirmation)', async () => {
    mocks.appData = makeApp({ status: 'stopped' });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /start app/i }));

    expect(mocks.startMutate).toHaveBeenCalledWith('test-app');
  });

  it('shows confirmation dialog before stopping', async () => {
    mocks.appData = makeApp({ status: 'active' });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /stop app/i }));

    expect(mocks.confirm).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Stop App',
        variant: 'danger',
      })
    );
  });

  it('stops app after confirmation', async () => {
    mocks.appData = makeApp({ status: 'active' });
    mocks.confirm.mockResolvedValue(true);

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /stop app/i }));

    await waitFor(() => {
      expect(mocks.stopMutate).toHaveBeenCalledWith('test-app');
    });
  });

  it('does not stop app when confirmation is declined', async () => {
    mocks.appData = makeApp({ status: 'active' });
    mocks.confirm.mockResolvedValue(false);

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /stop app/i }));

    await waitFor(() => {
      expect(mocks.stopMutate).not.toHaveBeenCalled();
    });
  });

  it('shows confirmation dialog before deleting', async () => {
    mocks.appData = makeApp({ status: 'stopped' });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /delete app/i }));

    expect(mocks.confirm).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Delete App',
        variant: 'danger',
      })
    );
  });

  it('navigates back after successful deletion', async () => {
    mocks.appData = makeApp({ status: 'stopped' });
    mocks.confirm.mockResolvedValue(true);
    mocks.deleteMutate.mockImplementation(
      (_name: string, opts?: { onSuccess?: () => void }) => opts?.onSuccess?.()
    );

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /delete app/i }));

    await waitFor(() => {
      expect(onBack).toHaveBeenCalled();
    });
  });

  it('shows app error message when present', () => {
    mocks.appData = makeApp({ error_message: 'Build failed', status: 'error' });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByText('Build failed')).toBeInTheDocument();
  });

  it('renders back button with accessible label', () => {
    mocks.appData = makeApp();

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByRole('button', { name: /back to apps list/i })).toBeInTheDocument();
  });

  it('navigates back when back button is clicked', async () => {
    mocks.appData = makeApp();

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    await userEvent.click(screen.getByRole('button', { name: /back to apps list/i }));

    expect(onBack).toHaveBeenCalled();
  });

  it('displays port as dash when null', () => {
    mocks.appData = makeApp({ port: null });

    render(<AppDetailView appName="test-app" onBack={onBack} />);

    expect(screen.getByText('—')).toBeInTheDocument();
  });
});
