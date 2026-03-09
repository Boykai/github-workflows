import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';

import { RepoConfigPanel } from './RepoConfigPanel';
import { McpPresetsGallery } from './McpPresetsGallery';
import { GitHubToolsetSelector } from './GitHubToolsetSelector';

describe('RepoConfigPanel', () => {
  it('renders repository MCP servers and source paths', () => {
    render(
      <RepoConfigPanel
        repoConfig={{
          paths_checked: ['.copilot/mcp.json', '.vscode/mcp.json'],
          available_paths: ['.copilot/mcp.json'],
          primary_path: '.copilot/mcp.json',
          servers: [
            {
              name: 'github',
              config: {
                type: 'http',
                url: 'https://api.githubcopilot.com/mcp/readonly',
              },
              source_paths: ['.copilot/mcp.json'],
            },
          ],
        }}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText('Current repository config')).toBeInTheDocument();
    expect(screen.getByText('github')).toBeInTheDocument();
    expect(screen.getByText('https://api.githubcopilot.com/mcp/readonly')).toBeInTheDocument();
    expect(screen.getAllByText('.copilot/mcp.json').length).toBeGreaterThan(0);
  });

  it('exposes edit and delete actions for existing repository MCPs', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(
      <RepoConfigPanel
        repoConfig={{
          paths_checked: ['.copilot/mcp.json', '.vscode/mcp.json'],
          available_paths: ['.copilot/mcp.json'],
          primary_path: '.copilot/mcp.json',
          servers: [
            {
              name: 'github',
              config: {
                type: 'http',
                url: 'https://api.githubcopilot.com/mcp/readonly',
              },
              source_paths: ['.copilot/mcp.json'],
            },
          ],
        }}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        onEdit={onEdit}
        onDelete={onDelete}
        managedServerNames={['github']}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Edit repository MCP github' }));
    await user.click(screen.getByRole('button', { name: 'Delete repository MCP github' }));

    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ name: 'github' }));
    expect(onDelete).toHaveBeenCalledWith(expect.objectContaining({ name: 'github' }));
    expect(screen.getByText('Managed')).toBeInTheDocument();
  });
});

describe('McpPresetsGallery', () => {
  it('calls onSelectPreset when a preset is chosen', async () => {
    const user = userEvent.setup();
    const onSelectPreset = vi.fn();
    render(
      <McpPresetsGallery
        presets={[
          {
            id: 'github-readonly',
            name: 'GitHub MCP Server',
            description: 'Read-only GitHub MCP server',
            category: 'GitHub',
            icon: 'github',
            config_content: '{"mcpServers":{}}',
          },
        ]}
        isLoading={false}
        error={null}
        onSelectPreset={onSelectPreset}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Use preset' }));

    expect(onSelectPreset).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'github-readonly', name: 'GitHub MCP Server' }),
    );
  });
});

describe('GitHubToolsetSelector', () => {
  it('creates a GitHub MCP config with selected toolsets', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<GitHubToolsetSelector onCreate={onCreate} isSubmitting={false} />);

    await user.click(screen.getByRole('button', { name: 'users' }));
    await user.click(screen.getByRole('button', { name: 'Create GitHub MCP tool' }));

    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'GitHub MCP Server',
        config_content: expect.stringContaining('X-MCP-Toolsets'),
      }),
    );
    expect(onCreate.mock.calls[0][0].config_content).toContain('users');
  });

  it('marks toolset buttons with pressed state', () => {
    render(<GitHubToolsetSelector onCreate={vi.fn().mockResolvedValue(undefined)} isSubmitting={false} />);

    expect(screen.getByRole('button', { name: 'repos' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'users' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('shows a local error when create fails', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockRejectedValue(new Error('Create failed'));
    render(<GitHubToolsetSelector onCreate={onCreate} isSubmitting={false} />);

    await user.click(screen.getByRole('button', { name: 'Create GitHub MCP tool' }));

    await waitFor(() => {
      expect(screen.getByText('Create failed')).toBeInTheDocument();
    });
  });
});