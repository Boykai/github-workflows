import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { ApiError } from '@/services/api';
import { AppDetailView } from './AppDetailView';
import type { App } from '@/types/apps';

const mocks = vi.hoisted(() => ({
  useAppReturn: {
    data: null as App | null,
    isLoading: false,
    error: null as unknown,
    refetch: vi.fn(),
  },
  startMutate: vi.fn(),
  stopMutate: vi.fn(),
  deleteApp: vi.fn(),
  confirm: vi.fn(),
  getErrorMessage: vi.fn((_error: unknown, fallback: string) => fallback),
  isRateLimitApiError: vi.fn(() => false),
  onBack: vi.fn(),
}));

vi.mock('@/hooks/useApps', () => ({
  useApp: () => mocks.useAppReturn,
  useStartApp: () => ({ mutate: mocks.startMutate, isPending: false }),
  useStopApp: () => ({ mutate: mocks.stopMutate, isPending: false }),
  useUndoableDeleteApp: () => ({ deleteApp: mocks.deleteApp, pendingIds: new Set<string>() }),
  getErrorMessage: mocks.getErrorMessage,
}));

vi.mock('@/hooks/useConfirmation', () => ({
  useConfirmation: () => ({ confirm: mocks.confirm }),
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { login: 'test-user' }, isLoading: false, isAuthenticated: true }),
}));

vi.mock('@/utils/rateLimit', () => ({
  isRateLimitApiError: mocks.isRateLimitApiError,
}));

vi.mock('./AppPreview', () => ({
  AppPreview: ({
    port,
    appName,
    isActive,
  }: {
    port: number | null;
    appName: string;
    isActive: boolean;
  }) => <div data-testid="app-preview">{`${appName}:${String(port)}:${String(isActive)}`}</div>,
}));

vi.mock('@/components/activity/EntityHistoryPanel', () => ({
  EntityHistoryPanel: () => null,
}));

const baseApp: App = {
  name: 'demo-app',
  display_name: 'Demo App',
  description: 'App description',
  directory_path: '/apps/demo-app',
  associated_pipeline_id: null,
  status: 'stopped',
  repo_type: 'same-repo',
  external_repo_url: null,
  port: 3000,
  error_message: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('AppDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.useAppReturn = {
      data: baseApp,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    };
    mocks.confirm.mockResolvedValue(true);
    mocks.getErrorMessage.mockImplementation((_error: unknown, fallback: string) => fallback);
    mocks.isRateLimitApiError.mockReturnValue(false);
  });

  it('shows a loading state while app details are fetched', () => {
    mocks.useAppReturn = {
      data: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    };

    render(<AppDetailView appName="demo-app" onBack={mocks.onBack} />);

    expect(screen.getByText('Loading app details…')).toBeInTheDocument();
  });

  it('shows the generic error state and lets the user retry or go back', async () => {
    const refetch = vi.fn();
    mocks.useAppReturn = {
      data: null,
      isLoading: false,
      error: new Error('boom'),
      refetch,
    };

    render(<AppDetailView appName="demo-app" onBack={mocks.onBack} />);

    expect(
      screen.getByText('Could not load app details. The app may not exist or an error occurred.')
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /retry/i }));
    await userEvent.click(screen.getByRole('button', { name: /back to apps/i }));

    expect(refetch).toHaveBeenCalledOnce();
    expect(mocks.onBack).toHaveBeenCalledOnce();
  });

  it('shows a rate limit specific message for rate-limited errors', () => {
    mocks.useAppReturn = {
      data: null,
      isLoading: false,
      error: new ApiError(429, { error: 'Slow down' }),
      refetch: vi.fn(),
    };
    mocks.isRateLimitApiError.mockReturnValue(true);

    render(<AppDetailView appName="demo-app" onBack={mocks.onBack} />);

    expect(
      screen.getByText('Rate limit exceeded. Please wait a moment before trying again.')
    ).toBeInTheDocument();
  });

  it('renders app metadata and preview details', () => {
    render(<AppDetailView appName="demo-app" onBack={mocks.onBack} />);

    expect(screen.getByRole('heading', { name: 'Demo App' })).toBeInTheDocument();
    expect(screen.getByText('App description')).toBeInTheDocument();
    expect(screen.getByText('same-repo')).toBeInTheDocument();
    expect(screen.getByText('3000')).toBeInTheDocument();
    expect(screen.getByTestId('app-preview')).toHaveTextContent('demo-app:3000:false');
  });

  it('starts a stopped app and shows success feedback', async () => {
    mocks.startMutate.mockImplementation((_appName: string, options?: { onSuccess?: () => void }) =>
      options?.onSuccess?.()
    );

    render(<AppDetailView appName="demo-app" onBack={mocks.onBack} />);

    await userEvent.click(screen.getByRole('button', { name: 'Start app Demo App' }));

    expect(mocks.startMutate).toHaveBeenCalledWith(
      'demo-app',
      expect.objectContaining({ onSuccess: expect.any(Function), onError: expect.any(Function) })
    );
    expect(screen.getByRole('status')).toHaveTextContent('App "Demo App" started successfully.');
  });

  it('confirms stop actions before mutating and shows errors when stopping fails', async () => {
    mocks.useAppReturn = {
      data: { ...baseApp, status: 'active' },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    };
    mocks.stopMutate.mockImplementation(
      (_appName: string, options?: { onError?: (error: Error) => void }) =>
        options?.onError?.(new Error('Could not stop.'))
    );

    render(<AppDetailView appName="demo-app" onBack={mocks.onBack} />);

    await userEvent.click(screen.getByRole('button', { name: 'Stop app Demo App' }));

    expect(mocks.confirm).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Stop App', variant: 'warning' })
    );
    expect(mocks.stopMutate).toHaveBeenCalledWith(
      'demo-app',
      expect.objectContaining({ onSuccess: expect.any(Function), onError: expect.any(Function) })
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Could not stop app "Demo App".');
  });

  it('deletes the app after confirmation and navigates back immediately', async () => {
    render(<AppDetailView appName="demo-app" onBack={mocks.onBack} />);

    await userEvent.click(screen.getByRole('button', { name: 'Delete app Demo App' }));

    await waitFor(() => {
      expect(mocks.deleteApp).toHaveBeenCalledWith('demo-app', 'Demo App');
      expect(mocks.onBack).toHaveBeenCalledOnce();
    });
  });
});
