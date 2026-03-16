import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { ApiError } from '@/services/api';
import type { McpToolConfig } from '@/types';

import { RepoConfigPanel } from './RepoConfigPanel';
import { McpPresetsGallery } from './McpPresetsGallery';
import { GitHubMcpConfigGenerator } from './GitHubMcpConfigGenerator';
import { ToolCard } from './ToolCard';

function makeTool(
  overrides: Partial<McpToolConfig> & { config_content: string; is_active?: boolean }
): McpToolConfig {
  return {
    id: 'tool-1',
    name: 'Test Tool',
    description: 'A test tool',
    endpoint_url: '',
    sync_status: 'synced',
    sync_error: '',
    synced_at: '2026-01-01T00:00:00Z',
    github_repo_target: 'owner/repo',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

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

    await user.click(screen.getByRole('button', { name: 'Use GitHub MCP Server preset' }));

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
    expect(screen.getAllByText('Built-In', { selector: 'span' })).toHaveLength(4);
    expect(screen.getByText('No custom project MCPs yet')).toBeInTheDocument();
    const activeProjectCard = screen.getByText('Active project MCPs').closest('div');
    expect(activeProjectCard).not.toBeNull();
    expect(within(activeProjectCard!).getByText('2')).toBeInTheDocument();
  });

  it('includes user tools alongside built-in MCPs in generated config', () => {
    const tools = [
      makeTool({
        name: 'Custom MCP',
        description: 'A custom MCP server',
        config_content: JSON.stringify({
          mcpServers: {
            'my-server': {
              type: 'http',
              url: 'https://example.com/mcp',
              tools: ['*'],
            },
          },
        }),
      }),
    ];

    render(<GitHubMcpConfigGenerator tools={tools} />);

    expect(screen.getByText('my-server')).toBeInTheDocument();
    expect(screen.getByText('context7')).toBeInTheDocument();
    expect(screen.getByText('CodeGraphContext')).toBeInTheDocument();
    expect(screen.getAllByText('Built-In', { selector: 'span' })).toHaveLength(4);
    // No empty state guidance when user tools are present
    expect(screen.queryByText(/No custom project MCPs yet/i)).not.toBeInTheDocument();
  });

  it('only includes active project MCPs in the generated config', () => {
    const tools = [
      makeTool({
        id: 'tool-active',
        name: 'Active MCP',
        description: 'Included server',
        config_content: JSON.stringify({
          mcpServers: {
            activeServer: {
              type: 'http',
              url: 'https://example.com/active',
            },
          },
        }),
        is_active: true,
      }),
      makeTool({
        id: 'tool-inactive',
        name: 'Inactive MCP',
        description: 'Excluded server',
        config_content: JSON.stringify({
          mcpServers: {
            inactiveServer: {
              type: 'http',
              url: 'https://example.com/inactive',
            },
          },
        }),
        is_active: false,
      }),
    ];

    render(<GitHubMcpConfigGenerator tools={tools} />);

    expect(screen.getByText('activeServer')).toBeInTheDocument();
    expect(screen.queryByText('inactiveServer')).not.toBeInTheDocument();
  });

  it('does not mark user overrides of built-in MCP keys as Built-In', () => {
    const tools = [
      makeTool({
        id: 'tool-override',
        name: 'Override Context7',
        description: 'User-provided Context7 override',
        config_content: JSON.stringify({
          mcpServers: {
            context7: {
              type: 'http',
              url: 'https://example.com/context7',
            },
          },
        }),
        is_active: true,
      }),
    ];

    render(<GitHubMcpConfigGenerator tools={tools} />);

    expect(screen.getByText('context7')).toBeInTheDocument();
    expect(screen.getByText('CodeGraphContext')).toBeInTheDocument();
    expect(screen.getAllByText('Built-In', { selector: 'span' })).toHaveLength(2);
  });

  it('shows copy to clipboard button', async () => {
    const user = userEvent.setup();
    // Mock clipboard API using defineProperty to work with happy-dom
    const writeText = vi.fn().mockResolvedValue(undefined);
    const originalClipboard = Object.getOwnPropertyDescriptor(navigator, 'clipboard');
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
      configurable: true,
    });

    try {
      render(<GitHubMcpConfigGenerator tools={[]} />);

      const copyButton = screen.getByRole('button', { name: /Copy to clipboard/ });
      expect(copyButton).toBeInTheDocument();

      await user.click(copyButton);

      expect(writeText).toHaveBeenCalledWith(expect.stringContaining('mcpServers'));
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    } finally {
      if (originalClipboard) {
        Object.defineProperty(navigator, 'clipboard', originalClipboard);
      } else {
        delete (navigator as Record<string, unknown>)['clipboard'];
      }
    }
  });

  it('falls back to document.execCommand when Clipboard API writes fail', async () => {
    const user = userEvent.setup();
    const originalClipboard = Object.getOwnPropertyDescriptor(navigator, 'clipboard');
    const originalExecCommand = Object.getOwnPropertyDescriptor(document, 'execCommand');
    const execCommandMock = vi.fn().mockReturnValue(true);
    const writeText = vi.fn().mockRejectedValue(new Error('Clipboard unavailable'));

    Object.defineProperty(document, 'execCommand', {
      value: execCommandMock,
      configurable: true,
      writable: true,
    });
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
      writable: true,
    });

    try {
      render(<GitHubMcpConfigGenerator tools={[]} />);

      await user.click(screen.getByRole('button', { name: /Copy to clipboard/i }));

      expect(writeText).toHaveBeenCalled();
      expect(execCommandMock).toHaveBeenCalledWith('copy');
      expect(screen.getByRole('button', { name: 'Copied' })).toBeInTheDocument();
    } finally {
      if (originalExecCommand) {
        Object.defineProperty(document, 'execCommand', originalExecCommand);
      } else {
        delete (document as Record<string, unknown>)['execCommand'];
      }
      if (originalClipboard) {
        Object.defineProperty(navigator, 'clipboard', originalClipboard);
      } else {
        delete (navigator as Record<string, unknown>)['clipboard'];
      }
    }
  });

  it('displays the generated JSON config with mcpServers', () => {
    render(<GitHubMcpConfigGenerator tools={[]} />);

    expect(screen.getByText(/mcpServers/)).toBeInTheDocument();

    const codeBlock = screen.getByTestId('github-mcp-config-code');
    expect(codeBlock.textContent).toContain('context7');
    expect(codeBlock.textContent).toContain('CodeGraphContext');
  });

  it('renders builtin metadata in the generated configuration JSON', () => {
    render(<GitHubMcpConfigGenerator tools={[]} />);

    const codeBlock = screen.getByTestId('github-mcp-config-code');
    expect(codeBlock.textContent).toContain('"builtin": true');
  });

  it('shows the syntax-highlighted code block guidance', () => {
    render(<GitHubMcpConfigGenerator tools={[]} />);

    expect(screen.getByText('Syntax-highlighted JSON ready to copy into GitHub.com.')).toBeInTheDocument();
    expect(screen.getByText('Built-In', { selector: 'p' })).toBeInTheDocument();
  });

  it('labels built-in MCPs inside the rendered configuration output', () => {
    render(<GitHubMcpConfigGenerator tools={[]} />);

    const codeBlock = screen.getByTestId('github-mcp-config-code');
    expect(within(codeBlock).getAllByText('Built-In')).toHaveLength(2);
    expect(
      within(codeBlock).getByLabelText('Context7 Built-In MCP', { selector: 'span' })
    ).toBeInTheDocument();
    expect(
      within(codeBlock).getByLabelText('Code Graph Context Built-In MCP', { selector: 'span' })
    ).toBeInTheDocument();
  });

  it('applies syntax-highlighting classes to JSON keys and values', () => {
    render(<GitHubMcpConfigGenerator tools={[]} />);

    expect(screen.getByText('"mcpServers"')).toHaveClass('text-sky-300');
    expect(screen.getByText('"https://mcp.context7.com/mcp"')).toHaveClass('text-emerald-300');
  });

  it('updates the generated config and empty state when active tools change', () => {
    const inactiveTool = makeTool({
      id: 'tool-realtime',
      name: 'Realtime MCP',
      is_active: false,
      config_content: JSON.stringify({
        mcpServers: {
          realtimeServer: {
            type: 'http',
            url: 'https://example.com/realtime',
          },
        },
      }),
    });

    const { rerender } = render(<GitHubMcpConfigGenerator tools={[inactiveTool]} />);
    expect(screen.queryByText('realtimeServer')).not.toBeInTheDocument();
    expect(screen.getByText('No custom project MCPs yet')).toBeInTheDocument();

    rerender(<GitHubMcpConfigGenerator tools={[{ ...inactiveTool, is_active: true }]} />);

    expect(screen.getByText('realtimeServer')).toBeInTheDocument();
    expect(screen.queryByText('No custom project MCPs yet')).not.toBeInTheDocument();
    const activeProjectCard = screen.getByText('Active project MCPs').closest('div');
    expect(activeProjectCard).not.toBeNull();
    expect(within(activeProjectCard!).getByText('3')).toBeInTheDocument();
  });
});

describe('RepoConfigPanel — states', () => {
  it('shows CelestialLoader when loading', () => {
    render(
      <RepoConfigPanel
        repoConfig={null}
        isLoading={true}
        error={null}
        onRefresh={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText('Loading repository MCP config')).toBeInTheDocument();
  });

  it('shows error message with retry button when an error occurs', async () => {
    const user = userEvent.setup();
    const onRefresh = vi.fn();

    render(
      <RepoConfigPanel
        repoConfig={null}
        isLoading={false}
        error="Network request failed"
        onRefresh={onRefresh}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(
      screen.getByText('Could not load repository config. Network request failed Please try again.')
    ).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRefresh).toHaveBeenCalled();
  });

  it('shows rate-limit message when rawError is a 429 ApiError', () => {
    const rateLimitError = new ApiError(429, { error: 'Too Many Requests' });

    render(
      <RepoConfigPanel
        repoConfig={null}
        isLoading={false}
        error="Too Many Requests"
        rawError={rateLimitError}
        onRefresh={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(
      screen.getByText('Rate limit reached. Please wait a few minutes before retrying.')
    ).toBeInTheDocument();
  });

  it('shows empty state when no servers are found', () => {
    render(
      <RepoConfigPanel
        repoConfig={{
          paths_checked: ['.copilot/mcp.json'],
          available_paths: [],
          primary_path: '.copilot/mcp.json',
          servers: [],
        }}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText('No MCP servers found in the repository yet.')).toBeInTheDocument();
  });
});

describe('McpPresetsGallery — states', () => {
  it('shows CelestialLoader when loading', () => {
    render(
      <McpPresetsGallery
        presets={[]}
        isLoading={true}
        error={null}
        onSelectPreset={vi.fn()}
      />
    );

    expect(screen.getByText('Loading presets')).toBeInTheDocument();
  });

  it('shows error message when an error occurs', () => {
    render(
      <McpPresetsGallery
        presets={[]}
        isLoading={false}
        error="Connection refused"
        onSelectPreset={vi.fn()}
      />
    );

    expect(
      screen.getByText('Could not load presets. Connection refused Please try again.')
    ).toBeInTheDocument();
  });

  it('shows rate-limit message when rawError is a 429 ApiError', () => {
    const rateLimitError = new ApiError(429, { error: 'Rate limited' });

    render(
      <McpPresetsGallery
        presets={[]}
        isLoading={false}
        error="Rate limited"
        rawError={rateLimitError}
        onSelectPreset={vi.fn()}
      />
    );

    expect(
      screen.getByText('Rate limit reached. Please wait a few minutes before retrying.')
    ).toBeInTheDocument();
  });

  it('shows retry button only when onRetry callback is provided', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    render(
      <McpPresetsGallery
        presets={[]}
        isLoading={false}
        error="Server error"
        onSelectPreset={vi.fn()}
        onRetry={onRetry}
      />
    );

    const retryButton = screen.getByRole('button', { name: 'Retry' });
    expect(retryButton).toBeInTheDocument();
    await user.click(retryButton);
    expect(onRetry).toHaveBeenCalled();
  });

  it('does not show retry button when onRetry is not provided', () => {
    render(
      <McpPresetsGallery
        presets={[]}
        isLoading={false}
        error="Server error"
        onSelectPreset={vi.fn()}
      />
    );

    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument();
  });

  it('shows empty state when loaded with no presets', () => {
    render(
      <McpPresetsGallery
        presets={[]}
        isLoading={false}
        error={null}
        onSelectPreset={vi.fn()}
      />
    );

    expect(
      screen.getByText('No presets available yet. Upload a custom MCP configuration to get started.')
    ).toBeInTheDocument();
  });
});

describe('ToolCard', () => {
  const baseProps = {
    onEdit: vi.fn(),
    onSync: vi.fn(),
    onDelete: vi.fn(),
  };

  it('renders tool name and description', () => {
    const tool = makeTool({
      name: 'My MCP Server',
      description: 'A helpful tool',
      config_content: '{}',
    });

    render(<ToolCard tool={tool} {...baseProps} />);

    expect(screen.getByText('My MCP Server')).toBeInTheDocument();
    expect(screen.getByText('A helpful tool')).toBeInTheDocument();
  });

  it('shows sync status badge with screen reader text', () => {
    const tool = makeTool({
      sync_status: 'synced',
      config_content: '{}',
    });

    render(<ToolCard tool={tool} {...baseProps} />);

    expect(screen.getByText('Synced to GitHub')).toBeInTheDocument();
    expect(screen.getByText(/— Status: Synced/)).toBeInTheDocument();
  });

  it('shows sync error badge and error details', () => {
    const tool = makeTool({
      sync_status: 'error',
      sync_error: 'Repository not found',
      config_content: '{}',
    });

    render(<ToolCard tool={tool} {...baseProps} />);

    expect(screen.getByText('Sync Error')).toBeInTheDocument();
    expect(screen.getByText('Repository not found')).toBeInTheDocument();
  });

  it('disables sync button while syncing', () => {
    const tool = makeTool({ config_content: '{}' });

    render(<ToolCard tool={tool} {...baseProps} isSyncing={true} />);

    const syncButton = screen.getByRole('button', { name: 'Re-sync to GitHub' });
    expect(syncButton).toBeDisabled();
  });

  it('disables delete button while deleting', () => {
    const tool = makeTool({ config_content: '{}' });

    render(<ToolCard tool={tool} {...baseProps} isDeleting={true} />);

    const deleteButton = screen.getByRole('button', { name: 'Delete tool' });
    expect(deleteButton).toBeDisabled();
  });
});
