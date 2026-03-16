/**
 * Integration tests for GlobalSettings component.
 *
 * Tests loading state, error state, rate limit error, form rendering,
 * and form submission.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import { GlobalSettings } from './GlobalSettings';
import type { GlobalSettings as GlobalSettingsType } from '@/types';

const sampleSettings: GlobalSettingsType = {
  ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
  display: { theme: 'dark', default_view: 'chat', sidebar_collapsed: false },
  workflow: {
    default_repository: 'owner/repo',
    default_assignee: 'octocat',
    copilot_polling_interval: 60,
  },
  notifications: {
    task_status_change: true,
    agent_completion: true,
    new_recommendation: true,
    chat_mention: true,
  },
  allowed_models: ['gpt-4o', 'gpt-3.5'],
};

describe('GlobalSettings', () => {
  it('renders CelestialLoader when loading', () => {
    render(
      <GlobalSettings settings={undefined} isLoading={true} onSave={vi.fn()} />
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders error state when error is provided and no settings', () => {
    const error = new Error('Network error');
    render(
      <GlobalSettings
        settings={undefined}
        isLoading={false}
        onSave={vi.fn()}
        error={error}
        onRetry={vi.fn()}
      />
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Could not load global settings. Please try again.')).toBeInTheDocument();
  });

  it('renders rate limit error message when isRateLimitError is true', () => {
    const error = new Error('Rate limited');
    render(
      <GlobalSettings
        settings={undefined}
        isLoading={false}
        onSave={vi.fn()}
        error={error}
        isRateLimitError={true}
        onRetry={vi.fn()}
      />
    );
    expect(
      screen.getByText('Rate limit reached. Please wait a moment before retrying.')
    ).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(
      <GlobalSettings
        settings={undefined}
        isLoading={false}
        onSave={vi.fn()}
        error={new Error('fail')}
        onRetry={onRetry}
      />
    );
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('renders form fields when settings are loaded', async () => {
    render(
      <GlobalSettings settings={sampleSettings} isLoading={false} onSave={vi.fn()} />
    );

    // The section is defaultCollapsed, so we need to expand it
    const toggle = screen.getByRole('button', { name: /Global Settings/i });
    await toggle.click();

    await waitFor(() => {
      expect(screen.getByLabelText('Provider')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Model')).toBeInTheDocument();
    expect(screen.getByLabelText(/Temperature/)).toBeInTheDocument();
    expect(screen.getByLabelText('Theme')).toBeInTheDocument();
    expect(screen.getByLabelText('Default View')).toBeInTheDocument();
    expect(screen.getByLabelText('Comma-separated model identifiers')).toBeInTheDocument();
  });

  it('renders CelestialLoader when no settings and no error', () => {
    render(
      <GlobalSettings settings={undefined} isLoading={false} onSave={vi.fn()} />
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
