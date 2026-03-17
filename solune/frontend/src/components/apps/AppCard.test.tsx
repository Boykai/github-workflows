import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { AppCard } from './AppCard';
import type { App } from '@/types/apps';

const baseApp: App = {
  name: 'test-app',
  display_name: 'Test App',
  description: 'A test application',
  directory_path: '/apps/test-app',
  associated_pipeline_id: null,
  status: 'stopped',
  repo_type: 'same-repo',
  external_repo_url: null,
  port: 3000,
  error_message: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const handlers = {
  onSelect: vi.fn(),
  onStart: vi.fn(),
  onStop: vi.fn(),
  onDelete: vi.fn(),
};

describe('AppCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the app name and description', () => {
    render(<AppCard app={baseApp} {...handlers} />);
    expect(screen.getByText('Test App')).toBeInTheDocument();
    expect(screen.getByText('A test application')).toBeInTheDocument();
  });

  it('shows the status badge', () => {
    render(<AppCard app={baseApp} {...handlers} />);
    expect(screen.getByText('Stopped')).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<AppCard app={baseApp} {...handlers} />);
    await expectNoA11yViolations(container);
  });

  it('falls back to a default description when one is missing', () => {
    render(<AppCard app={{ ...baseApp, description: null }} {...handlers} />);
    expect(screen.getByText('No description')).toBeInTheDocument();
  });

  it('calls onSelect when the overlay button is clicked', async () => {
    const user = userEvent.setup();
    render(<AppCard app={baseApp} {...handlers} />);

    await user.click(screen.getByRole('button', { name: 'View app Test App' }));

    expect(handlers.onSelect).toHaveBeenCalledWith('test-app');
  });

  it('shows start and delete actions for stopped apps', () => {
    render(<AppCard app={baseApp} {...handlers} />);

    expect(screen.getByRole('button', { name: 'Start app Test App' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete app Test App' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Stop app Test App' })).not.toBeInTheDocument();
  });

  it('calls onStart when the start button is clicked', async () => {
    const user = userEvent.setup();
    render(<AppCard app={baseApp} {...handlers} />);

    await user.click(screen.getByRole('button', { name: 'Start app Test App' }));

    expect(handlers.onStart).toHaveBeenCalledWith('test-app');
  });

  it('disables start and delete buttons while pending', () => {
    render(<AppCard app={baseApp} {...handlers} isStartPending isDeletePending />);

    expect(screen.getByRole('button', { name: 'Start app Test App' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Delete app Test App' })).toBeDisabled();
  });

  it('shows stop action for active apps and hides delete', async () => {
    const user = userEvent.setup();
    render(
      <AppCard app={{ ...baseApp, status: 'active' }} {...handlers} isStopPending={false} />
    );

    expect(screen.getByRole('button', { name: 'Stop app Test App' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Delete app Test App' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Stop app Test App' }));
    expect(handlers.onStop).toHaveBeenCalledWith('test-app');
  });

  it('disables the stop action while a stop request is pending', () => {
    render(<AppCard app={{ ...baseApp, status: 'active' }} {...handlers} isStopPending />);

    expect(screen.getByRole('button', { name: 'Stop app Test App' })).toBeDisabled();
  });
});
