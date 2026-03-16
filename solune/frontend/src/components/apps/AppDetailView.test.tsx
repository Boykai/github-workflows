import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent, waitFor, within } from '@/test/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { AppDetailView } from './AppDetailView';
import type { App } from '@/types/apps';

const mocks = vi.hoisted(() => ({
  onBack: vi.fn(),
  startMutate: vi.fn(),
  stopMutate: vi.fn(),
  deleteMutate: vi.fn(),
  refetch: vi.fn(),
}));

vi.mock('@/hooks/useApps', () => ({
  useApp: vi.fn(),
  useStartApp: () => ({ mutate: mocks.startMutate, isPending: false }),
  useStopApp: () => ({ mutate: mocks.stopMutate, isPending: false }),
  useDeleteApp: () => ({ mutate: mocks.deleteMutate, isPending: false }),
}));

import { useApp } from '@/hooks/useApps';
const mockUseApp = vi.mocked(useApp);

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

function createApp(overrides: Partial<App> = {}): App {
  return {
    name: 'my-app',
    display_name: 'My App',
    description: 'A test application',
    directory_path: '/apps/my-app',
    associated_pipeline_id: null,
    status: 'stopped',
    repo_type: 'same-repo',
    external_repo_url: null,
    port: null,
    error_message: null,
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-01-15T10:00:00Z',
    ...overrides,
  };
}

describe('AppDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseApp.mockReturnValue({
      data: createApp(),
      isLoading: false,
      error: null,
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);
  });

  it('shows a loading indicator while data is loading', () => {
    mockUseApp.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows an error state with retry button when loading fails', () => {
    mockUseApp.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText(/could not load app details/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('calls refetch when the retry button is clicked', async () => {
    mockUseApp.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(mocks.refetch).toHaveBeenCalledOnce();
  });

  it('renders app name and description when loaded', () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByRole('heading', { name: 'My App' })).toBeInTheDocument();
    expect(screen.getByText('A test application')).toBeInTheDocument();
  });

  it('renders metadata: status, port, and created date', () => {
    mockUseApp.mockReturnValue({
      data: createApp({ status: 'active', port: 3000 }),
      isLoading: false,
      error: null,
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('3000')).toBeInTheDocument();
  });

  it('calls onBack when the Back button is clicked', async () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /back to apps/i }));
    expect(mocks.onBack).toHaveBeenCalledOnce();
  });

  it('shows Start button for a stopped app', () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByRole('button', { name: /start my app/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /stop my app/i })).not.toBeInTheDocument();
  });

  it('shows Stop button for an active app', () => {
    mockUseApp.mockReturnValue({
      data: createApp({ status: 'active', port: 3000 }),
      isLoading: false,
      error: null,
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByRole('button', { name: /stop my app/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /start my app/i })).not.toBeInTheDocument();
  });

  it('calls startMutation when Start is clicked', async () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /start my app/i }));
    expect(mocks.startMutate).toHaveBeenCalledWith('my-app');
  });

  it('shows a confirmation dialog before stopping', async () => {
    mockUseApp.mockReturnValue({
      data: createApp({ status: 'active', port: 3000 }),
      isLoading: false,
      error: null,
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /stop my app/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(mocks.stopMutate).not.toHaveBeenCalled();
  });

  it('calls stopMutation after confirming stop', async () => {
    mockUseApp.mockReturnValue({
      data: createApp({ status: 'active', port: 3000 }),
      isLoading: false,
      error: null,
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /stop my app/i }));
    const dialog = screen.getByRole('dialog');
    await userEvent.click(within(dialog).getByRole('button', { name: /^stop$/i }));
    expect(mocks.stopMutate).toHaveBeenCalledWith('my-app');
  });

  it('shows a confirmation dialog before deleting', async () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /delete my app/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(mocks.deleteMutate).not.toHaveBeenCalled();
  });

  it('calls deleteMutation after confirming deletion', async () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /delete my app/i }));
    const dialog = screen.getByRole('dialog');
    await userEvent.click(within(dialog).getByRole('button', { name: /^delete$/i }));
    expect(mocks.deleteMutate).toHaveBeenCalledWith('my-app', expect.any(Object));
  });

  it('cancels deletion when cancel is clicked in the confirmation', async () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    await userEvent.click(screen.getByRole('button', { name: /delete my app/i }));
    const dialog = screen.getByRole('dialog');
    await userEvent.click(within(dialog).getByRole('button', { name: /cancel/i }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    expect(mocks.deleteMutate).not.toHaveBeenCalled();
  });

  it('shows the error_message when the app has an error', () => {
    mockUseApp.mockReturnValue({
      data: createApp({ status: 'error', error_message: 'Build failed: missing dependency' }),
      isLoading: false,
      error: null,
      refetch: mocks.refetch,
    } as ReturnType<typeof useApp>);

    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('Build failed: missing dependency')).toBeInTheDocument();
  });

  it('shows a dash for port when port is null', () => {
    render(<AppDetailView appName="my-app" onBack={mocks.onBack} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('—')).toBeInTheDocument();
  });
});
