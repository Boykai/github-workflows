/**
 * Tests for AdminTab component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { AdminTab } from './AdminTab';
import type { GlobalSettings, GlobalSettingsUpdate } from '@/types';

// ── Mock child components ──

vi.mock('./GlobalSettings', () => ({
  GlobalSettings: ({ isLoading }: { isLoading: boolean }) => (
    <div data-testid="global-settings">{isLoading ? 'Loading…' : 'Global Settings'}</div>
  ),
}));

vi.mock('./ProjectSettings', () => ({
  ProjectSettings: ({ selectedProjectId }: { selectedProjectId?: string }) => (
    <div data-testid="project-settings">Project: {selectedProjectId ?? 'none'}</div>
  ),
}));

// ── Fixtures ──

const mockGlobalSettings: GlobalSettings = {
  admin_github_user_id: '12345',
  allowed_models: [],
  default_ai: {
    provider: 'copilot',
    model: 'gpt-4',
    agent_model: 'gpt-4',
    temperature: 0.7,
  },
};

const mockProjects = [
  { project_id: 'PVT_1', name: 'Project One' },
  { project_id: 'PVT_2', name: 'Project Two' },
];

describe('AdminTab', () => {
  const onGlobalSave = vi.fn<(u: GlobalSettingsUpdate) => Promise<void>>().mockResolvedValue(undefined);

  it('renders GlobalSettings component', () => {
    render(
      <AdminTab
        globalSettings={mockGlobalSettings}
        globalLoading={false}
        onGlobalSave={onGlobalSave}
        projects={mockProjects}
        selectedProjectId="PVT_1"
      />
    );
    expect(screen.getByTestId('global-settings')).toBeInTheDocument();
    expect(screen.getByText('Global Settings')).toBeInTheDocument();
  });

  it('renders ProjectSettings component', () => {
    render(
      <AdminTab
        globalSettings={mockGlobalSettings}
        globalLoading={false}
        onGlobalSave={onGlobalSave}
        projects={mockProjects}
        selectedProjectId="PVT_1"
      />
    );
    expect(screen.getByTestId('project-settings')).toBeInTheDocument();
    expect(screen.getByText('Project: PVT_1')).toBeInTheDocument();
  });

  it('passes loading state to GlobalSettings', () => {
    render(
      <AdminTab
        globalSettings={mockGlobalSettings}
        globalLoading={true}
        onGlobalSave={onGlobalSave}
        projects={mockProjects}
      />
    );
    expect(screen.getByText('Loading…')).toBeInTheDocument();
  });

  it('renders without selected project ID', () => {
    render(
      <AdminTab
        globalSettings={mockGlobalSettings}
        globalLoading={false}
        onGlobalSave={onGlobalSave}
        projects={mockProjects}
      />
    );
    expect(screen.getByText('Project: none')).toBeInTheDocument();
  });
});
