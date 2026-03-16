/**
 * Tests for AppCard component.
 * Covers: rendering, status badges, action buttons, disabled states, truncation, edge cases.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { AppCard } from './AppCard';
import type { App } from '@/types/apps';

function makeApp(overrides: Partial<App> = {}): App {
  return {
    name: 'my-app',
    display_name: 'My App',
    description: 'A cool application',
    directory_path: '/apps/my-app',
    associated_pipeline_id: null,
    status: 'active',
    repo_type: 'same-repo',
    external_repo_url: null,
    port: 3000,
    error_message: null,
    created_at: '2026-03-15T10:00:00Z',
    updated_at: '2026-03-15T12:00:00Z',
    ...overrides,
  };
}

describe('AppCard', () => {
  const defaultProps = {
    onSelect: vi.fn(),
    onStart: vi.fn(),
    onStop: vi.fn(),
    onDelete: vi.fn(),
  };

  beforeEach(() => vi.clearAllMocks());

  it('renders app name and description', () => {
    render(<AppCard app={makeApp()} {...defaultProps} />);

    expect(screen.getByText('My App')).toBeInTheDocument();
    expect(screen.getByText('A cool application')).toBeInTheDocument();
  });

  it('renders "No description" when description is empty', () => {
    render(<AppCard app={makeApp({ description: '' })} {...defaultProps} />);

    expect(screen.getByText('No description')).toBeInTheDocument();
  });

  it('shows Active status badge for active apps', () => {
    render(<AppCard app={makeApp({ status: 'active' })} {...defaultProps} />);

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('shows Stopped status badge for stopped apps', () => {
    render(<AppCard app={makeApp({ status: 'stopped' })} {...defaultProps} />);

    expect(screen.getByText('Stopped')).toBeInTheDocument();
  });

  it('shows Creating status badge for creating apps', () => {
    render(<AppCard app={makeApp({ status: 'creating' })} {...defaultProps} />);

    expect(screen.getByText('Creating')).toBeInTheDocument();
  });

  it('shows Error status badge for error apps', () => {
    render(<AppCard app={makeApp({ status: 'error' })} {...defaultProps} />);

    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('shows Stop button for active apps', () => {
    render(<AppCard app={makeApp({ status: 'active' })} {...defaultProps} />);

    expect(screen.getByRole('button', { name: /stop app/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /start app/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /delete app/i })).not.toBeInTheDocument();
  });

  it('shows Start and Delete buttons for stopped apps', () => {
    render(<AppCard app={makeApp({ status: 'stopped' })} {...defaultProps} />);

    expect(screen.getByRole('button', { name: /start app/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete app/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /stop app/i })).not.toBeInTheDocument();
  });

  it('calls onSelect when card is clicked', async () => {
    render(<AppCard app={makeApp()} {...defaultProps} />);

    await userEvent.click(screen.getByText('My App'));

    expect(defaultProps.onSelect).toHaveBeenCalledWith('my-app');
  });

  it('calls onStart when Start button is clicked', async () => {
    render(<AppCard app={makeApp({ status: 'stopped' })} {...defaultProps} />);

    await userEvent.click(screen.getByRole('button', { name: /start app/i }));

    expect(defaultProps.onStart).toHaveBeenCalledWith('my-app');
    expect(defaultProps.onSelect).not.toHaveBeenCalled();
  });

  it('calls onStop when Stop button is clicked', async () => {
    render(<AppCard app={makeApp({ status: 'active' })} {...defaultProps} />);

    await userEvent.click(screen.getByRole('button', { name: /stop app/i }));

    expect(defaultProps.onStop).toHaveBeenCalledWith('my-app');
    expect(defaultProps.onSelect).not.toHaveBeenCalled();
  });

  it('calls onDelete when Delete button is clicked', async () => {
    render(<AppCard app={makeApp({ status: 'stopped' })} {...defaultProps} />);

    await userEvent.click(screen.getByRole('button', { name: /delete app/i }));

    expect(defaultProps.onDelete).toHaveBeenCalledWith('my-app');
    expect(defaultProps.onSelect).not.toHaveBeenCalled();
  });

  it('disables Start button when isStartPending is true', () => {
    render(
      <AppCard
        app={makeApp({ status: 'stopped' })}
        {...defaultProps}
        isStartPending
      />
    );

    expect(screen.getByRole('button', { name: /start app/i })).toBeDisabled();
  });

  it('disables Stop button when isStopPending is true', () => {
    render(
      <AppCard
        app={makeApp({ status: 'active' })}
        {...defaultProps}
        isStopPending
      />
    );

    expect(screen.getByRole('button', { name: /stop app/i })).toBeDisabled();
  });

  it('disables Delete button when isDeletePending is true', () => {
    render(
      <AppCard
        app={makeApp({ status: 'stopped' })}
        {...defaultProps}
        isDeletePending
      />
    );

    expect(screen.getByRole('button', { name: /delete app/i })).toBeDisabled();
  });

  it('handles app with null port, null error_message, null pipeline', () => {
    render(
      <AppCard
        app={makeApp({
          port: null,
          error_message: null,
          associated_pipeline_id: null,
        })}
        {...defaultProps}
      />
    );

    expect(screen.getByText('My App')).toBeInTheDocument();
  });

  it('handles app with very long name', () => {
    const longName = 'A'.repeat(64);
    render(
      <AppCard
        app={makeApp({ display_name: longName })}
        {...defaultProps}
      />
    );

    expect(screen.getByText(longName)).toBeInTheDocument();
  });

  it('has an actions toolbar with aria-label', () => {
    render(<AppCard app={makeApp()} {...defaultProps} />);

    expect(screen.getByRole('toolbar')).toHaveAttribute(
      'aria-label',
      'Actions for My App'
    );
  });
});
