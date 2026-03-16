import { describe, expect, it, vi } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import type { GlobalSettings as GlobalSettingsType } from '@/types';
import { GlobalSettings } from './GlobalSettings';

const settingsFixture: GlobalSettingsType = {
  ai: {
    provider: 'copilot',
    model: 'gpt-4o',
    temperature: 0.7,
    agent_model: 'gpt-4o-mini',
  },
  display: {
    theme: 'dark',
    default_view: 'board',
    sidebar_collapsed: true,
  },
  workflow: {
    default_repository: 'octo/repo',
    default_assignee: 'copilot',
    copilot_polling_interval: 60,
  },
  notifications: {
    task_status_change: true,
    agent_completion: false,
    new_recommendation: true,
    chat_mention: false,
  },
  allowed_models: ['gpt-4o', 'gpt-4.1'],
};

describe('GlobalSettings', () => {
  it('shows an accessible loader while global settings are loading', () => {
    render(<GlobalSettings settings={undefined} isLoading={true} onSave={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Global Settings' })).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading global settings…');
    expect(screen.queryByRole('button', { name: 'Save Settings' })).not.toBeInTheDocument();
  });

  it('describes the allowed models input after expanding the section', async () => {
    const user = userEvent.setup();
    render(<GlobalSettings settings={settingsFixture} isLoading={false} onSave={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Expand Global Settings' }));

    const input = screen.getByLabelText('Comma-separated model identifiers');
    expect(input).toHaveAttribute('aria-describedby', 'global-models-hint');
    expect(screen.getByText('List the model IDs users are permitted to select, separated by commas.')).toHaveAttribute(
      'id',
      'global-models-hint'
    );
  });

  it('submits trimmed allowed model identifiers when the section is saved', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);

    render(<GlobalSettings settings={settingsFixture} isLoading={false} onSave={onSave} />);

    await user.click(screen.getByRole('button', { name: 'Expand Global Settings' }));

    const input = screen.getByLabelText('Comma-separated model identifiers');
    await user.clear(input);
    await user.type(input, 'gpt-4o, gpt-5 , , claude-3');
    await user.click(screen.getByRole('button', { name: 'Save Settings' }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith({
        ai: { provider: 'copilot', model: 'gpt-4o', temperature: 0.7 },
        display: {
          theme: 'dark',
          default_view: 'board',
          sidebar_collapsed: true,
        },
        workflow: {
          default_repository: 'octo/repo',
          default_assignee: 'copilot',
          copilot_polling_interval: 60,
        },
        notifications: {
          task_status_change: true,
          agent_completion: false,
          new_recommendation: true,
          chat_mention: false,
        },
        allowed_models: ['gpt-4o', 'gpt-5', 'claude-3'],
      });
    });
  });
});
