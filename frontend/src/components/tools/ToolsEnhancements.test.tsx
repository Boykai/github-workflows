import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';

import { RepoConfigPanel } from './RepoConfigPanel';
import { McpPresetsGallery } from './McpPresetsGallery';
import { GitHubMcpConfigGenerator } from './GitHubMcpConfigGenerator';

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
      />
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
      />
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
      />
    );

    await user.click(screen.getByRole('button', { name: 'Use preset' }));

    expect(onSelectPreset).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'github-readonly', name: 'GitHub MCP Server' })
    );
  });
});

describe('GitHubMcpConfigGenerator', () => {
  it('renders built-in MCPs with Built-In badges when no tools are active', () => {
    render(<GitHubMcpConfigGenerator tools={[]} />);

    expect(screen.getByText('MCP Configuration for GitHub Agents')).toBeInTheDocument();
    expect(screen.getByText('context7')).toBeInTheDocument();
    expect(screen.getByText('CodeGraphContext')).toBeInTheDocument();
    expect(screen.getAllByText('Built-In')).toHaveLength(2);
    expect(screen.getByText(/No project MCP tools are active yet/)).toBeInTheDocument();
  });

  it('includes user tools alongside built-in MCPs in generated config', () => {
    const tools = [
      {
        id: 'tool-1',
        name: 'Custom MCP',
        description: 'A custom MCP server',
        endpoint_url: '',
        config_content: JSON.stringify({
          mcpServers: {
            'my-server': {
              type: 'http',
              url: 'https://example.com/mcp',
              tools: ['*'],
            },
          },
        }),
        sync_status: 'synced' as const,
        sync_error: '',
        synced_at: '2026-01-01T00:00:00Z',
        github_repo_target: 'owner/repo',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ];

    render(<GitHubMcpConfigGenerator tools={tools} />);

    expect(screen.getByText('my-server')).toBeInTheDocument();
    expect(screen.getByText('context7')).toBeInTheDocument();
    expect(screen.getByText('CodeGraphContext')).toBeInTheDocument();
    // Only built-ins get the badge
    expect(screen.getAllByText('Built-In')).toHaveLength(2);
    // No empty state guidance when user tools are present
    expect(screen.queryByText(/No project MCP tools are active yet/)).not.toBeInTheDocument();
  });

  it('shows copy to clipboard button', async () => {
    const user = userEvent.setup();
    // Mock clipboard API using defineProperty to work with happy-dom
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
      configurable: true,
    });

    render(<GitHubMcpConfigGenerator tools={[]} />);

    const copyButton = screen.getByRole('button', { name: /Copy to Clipboard/ });
    expect(copyButton).toBeInTheDocument();

    await user.click(copyButton);

    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('mcpServers'));
    expect(screen.getByText('Copied!')).toBeInTheDocument();
  });

  it('displays the generated JSON config with mcpServers', () => {
    render(<GitHubMcpConfigGenerator tools={[]} />);

    const pre = screen.getByText(/mcpServers/);
    expect(pre).toBeInTheDocument();
    expect(pre.textContent).toContain('context7');
    expect(pre.textContent).toContain('CodeGraphContext');
  });
});
