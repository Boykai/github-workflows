/**
 * Tests for PreferencesTab component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { PreferencesTab } from './PreferencesTab';
import type { EffectiveUserSettings, UserPreferencesUpdate } from '@/types';

// ── Mock child components ──
// Mock each sub-component to verify PreferencesTab correctly delegates.

vi.mock('./DisplayPreferences', () => ({
  DisplayPreferences: ({ settings }: { settings: unknown }) => (
    <div data-testid="display-preferences">Display: {JSON.stringify(settings)}</div>
  ),
}));

vi.mock('./WorkflowDefaults', () => ({
  WorkflowDefaults: ({ settings }: { settings: unknown }) => (
    <div data-testid="workflow-defaults">Workflow: {JSON.stringify(settings)}</div>
  ),
}));

vi.mock('./NotificationPreferences', () => ({
  NotificationPreferences: ({ settings }: { settings: unknown }) => (
    <div data-testid="notification-preferences">Notifications: {JSON.stringify(settings)}</div>
  ),
}));

vi.mock('./SignalConnection', () => ({
  SignalConnection: () => <div data-testid="signal-connection">Signal</div>,
}));

// ── Fixtures ──

const mockSettings: EffectiveUserSettings = {
  ai: {
    provider: 'copilot',
    model: 'gpt-4',
    agent_model: 'gpt-4',
    temperature: 0.7,
  },
  display: {
    theme: 'dark',
    compact_mode: false,
    show_timestamps: true,
    code_font_size: 14,
    enable_sounds: false,
    enable_animations: true,
    dashboard_layout: 'grid',
  },
  workflow: {
    auto_assign: true,
    require_review: false,
    default_priority: 'medium',
    auto_close_resolved: true,
    stale_days: 30,
    default_branch: 'main',
  },
  notifications: {
    email_enabled: true,
    slack_enabled: false,
    notify_on_mention: true,
    notify_on_assignment: true,
    digest_frequency: 'daily',
  },
};

describe('PreferencesTab', () => {
  const onUserSave = vi.fn<(u: UserPreferencesUpdate) => Promise<void>>().mockResolvedValue(undefined);

  it('renders DisplayPreferences with correct settings', () => {
    render(<PreferencesTab userSettings={mockSettings} onUserSave={onUserSave} />);
    expect(screen.getByTestId('display-preferences')).toBeInTheDocument();
  });

  it('renders WorkflowDefaults with correct settings', () => {
    render(<PreferencesTab userSettings={mockSettings} onUserSave={onUserSave} />);
    expect(screen.getByTestId('workflow-defaults')).toBeInTheDocument();
  });

  it('renders NotificationPreferences with correct settings', () => {
    render(<PreferencesTab userSettings={mockSettings} onUserSave={onUserSave} />);
    expect(screen.getByTestId('notification-preferences')).toBeInTheDocument();
  });

  it('renders SignalConnection', () => {
    render(<PreferencesTab userSettings={mockSettings} onUserSave={onUserSave} />);
    expect(screen.getByTestId('signal-connection')).toBeInTheDocument();
  });

  it('renders all four preference sections', () => {
    render(<PreferencesTab userSettings={mockSettings} onUserSave={onUserSave} />);
    expect(screen.getByTestId('display-preferences')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-defaults')).toBeInTheDocument();
    expect(screen.getByTestId('notification-preferences')).toBeInTheDocument();
    expect(screen.getByTestId('signal-connection')).toBeInTheDocument();
  });
});
