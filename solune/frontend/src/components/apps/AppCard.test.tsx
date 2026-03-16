import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent, within } from '@/test/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';
import { AppCard } from './AppCard';
import type { App } from '@/types/apps';

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

const mocks = vi.hoisted(() => ({
  onSelect: vi.fn(),
  onStart: vi.fn(),
  onStop: vi.fn(),
  onDelete: vi.fn(),
}));

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
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('AppCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders app display name and description', () => {
    render(
      <AppCard
        app={createApp()}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('My App')).toBeInTheDocument();
    expect(screen.getByText('A test application')).toBeInTheDocument();
  });

  it('renders "No description" when description is empty', () => {
    render(
      <AppCard
        app={createApp({ description: '' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('No description')).toBeInTheDocument();
  });

  it('shows Start and Delete buttons for a stopped app', () => {
    render(
      <AppCard
        app={createApp({ status: 'stopped' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /start my app/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete my app/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /stop my app/i })).not.toBeInTheDocument();
  });

  it('shows only Stop button for an active app', () => {
    render(
      <AppCard
        app={createApp({ status: 'active' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /stop my app/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /start my app/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /delete my app/i })).not.toBeInTheDocument();
  });

  it('shows Delete button for an app in error status', () => {
    render(
      <AppCard
        app={createApp({ status: 'error' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /delete my app/i })).toBeInTheDocument();
  });

  it('calls onSelect with the app name when card is clicked', async () => {
    render(
      <AppCard
        app={createApp()}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    // The card button contains all text; click the outermost card button (first button)
    const buttons = screen.getAllByRole('button');
    await userEvent.click(buttons[0]);
    expect(mocks.onSelect).toHaveBeenCalledWith('my-app');
  });

  it('calls onStart when Start is clicked and does not select the card', async () => {
    render(
      <AppCard
        app={createApp({ status: 'stopped' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    await userEvent.click(screen.getByRole('button', { name: /start my app/i }));
    expect(mocks.onStart).toHaveBeenCalledWith('my-app');
    expect(mocks.onSelect).not.toHaveBeenCalled();
  });

  it('calls onStop when Stop is clicked and does not select the card', async () => {
    render(
      <AppCard
        app={createApp({ status: 'active' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    await userEvent.click(screen.getByRole('button', { name: /stop my app/i }));
    expect(mocks.onStop).toHaveBeenCalledWith('my-app');
    expect(mocks.onSelect).not.toHaveBeenCalled();
  });

  it('shows a confirmation dialog before deleting', async () => {
    render(
      <AppCard
        app={createApp({ status: 'stopped' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    await userEvent.click(screen.getByRole('button', { name: /delete my app/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/delete app/i)).toBeInTheDocument();
    expect(mocks.onDelete).not.toHaveBeenCalled();
  });

  it('calls onDelete after confirming deletion', async () => {
    render(
      <AppCard
        app={createApp({ status: 'stopped' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    await userEvent.click(screen.getByRole('button', { name: /delete my app/i }));
    const confirmDialog = screen.getByRole('dialog');
    await userEvent.click(within(confirmDialog).getByRole('button', { name: /^delete$/i }));
    expect(mocks.onDelete).toHaveBeenCalledWith('my-app');
  });

  it('does not call onDelete when cancelling the delete confirmation', async () => {
    render(
      <AppCard
        app={createApp({ status: 'stopped' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    await userEvent.click(screen.getByRole('button', { name: /delete my app/i }));
    const confirmDialog = screen.getByRole('dialog');
    await userEvent.click(within(confirmDialog).getByRole('button', { name: /cancel/i }));
    expect(mocks.onDelete).not.toHaveBeenCalled();
  });

  it('renders the Stopped status badge for a stopped app', () => {
    render(
      <AppCard
        app={createApp({ status: 'stopped' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Stopped')).toBeInTheDocument();
  });

  it('renders the Active status badge for an active app', () => {
    render(
      <AppCard
        app={createApp({ status: 'active' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('has accessible aria-labels on action buttons', () => {
    render(
      <AppCard
        app={createApp({ status: 'stopped' })}
        onSelect={mocks.onSelect}
        onStart={mocks.onStart}
        onStop={mocks.onStop}
        onDelete={mocks.onDelete}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: 'Start My App' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete My App' })).toBeInTheDocument();
  });
});
