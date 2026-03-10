import { describe, expect, it } from 'vitest';
import type { McpToolConfig } from '@/types';
import {
  buildGitHubMcpConfig,
  extractServersFromTool,
  BUILTIN_MCPS,
} from './buildGitHubMcpConfig';

function makeTool(overrides: Partial<McpToolConfig> & { config_content: string }): McpToolConfig {
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

describe('extractServersFromTool', () => {
  it('extracts mcpServers from valid config_content', () => {
    const tool = makeTool({
      config_content: JSON.stringify({
        mcpServers: {
          github: { type: 'http', url: 'https://api.github.com/mcp' },
        },
      }),
    });

    const entries = extractServersFromTool(tool);
    expect(entries).toHaveLength(1);
    expect(entries[0].key).toBe('github');
    expect(entries[0].builtin).toBe(false);
    expect(entries[0].config).toEqual({ type: 'http', url: 'https://api.github.com/mcp' });
  });

  it('returns empty array for malformed JSON', () => {
    const tool = makeTool({ config_content: 'not-json' });
    expect(extractServersFromTool(tool)).toEqual([]);
  });

  it('returns empty array when mcpServers is missing', () => {
    const tool = makeTool({ config_content: JSON.stringify({ other: 'data' }) });
    expect(extractServersFromTool(tool)).toEqual([]);
  });

  it('extracts multiple servers from a single tool', () => {
    const tool = makeTool({
      config_content: JSON.stringify({
        mcpServers: {
          server1: { type: 'http', url: 'https://one.com' },
          server2: { type: 'sse', url: 'https://two.com' },
        },
      }),
    });

    const entries = extractServersFromTool(tool);
    expect(entries).toHaveLength(2);
    expect(entries.map((e) => e.key)).toEqual(['server1', 'server2']);
  });
});

describe('buildGitHubMcpConfig', () => {
  it('includes built-in MCPs when no tools are provided', () => {
    const { configJson, entries } = buildGitHubMcpConfig([]);

    expect(entries).toHaveLength(BUILTIN_MCPS.length);
    expect(entries.every((e) => e.builtin)).toBe(true);

    const parsed = JSON.parse(configJson) as {
      mcpServers: Record<string, { builtin?: boolean }>;
    };
    expect(parsed.mcpServers).toHaveProperty('context7');
    expect(parsed.mcpServers).toHaveProperty('CodeGraphContext');
    expect(parsed.mcpServers.context7.builtin).toBe(true);
    expect(parsed.mcpServers.CodeGraphContext.builtin).toBe(true);
  });

  it('merges user tools with built-in MCPs', () => {
    const tools = [
      makeTool({
        config_content: JSON.stringify({
          mcpServers: {
            'my-custom': { type: 'http', url: 'https://custom.com/mcp' },
          },
        }),
      }),
    ];

    const { configJson, entries } = buildGitHubMcpConfig(tools);

    expect(entries).toHaveLength(1 + BUILTIN_MCPS.length);
    expect(entries[0].key).toBe('my-custom');
    expect(entries[0].builtin).toBe(false);

    const parsed = JSON.parse(configJson) as { mcpServers: Record<string, unknown> };
    expect(parsed.mcpServers).toHaveProperty('my-custom');
    expect(parsed.mcpServers).toHaveProperty('context7');
    expect(parsed.mcpServers).toHaveProperty('CodeGraphContext');
  });

  it('user tool overrides built-in when keys collide', () => {
    const customContext7Config = { type: 'http', url: 'https://my-context7.com/mcp' };
    const tools = [
      makeTool({
        config_content: JSON.stringify({
          mcpServers: {
            context7: customContext7Config,
          },
        }),
      }),
    ];

    const { entries } = buildGitHubMcpConfig(tools);

    const context7Entry = entries.find((e) => e.key === 'context7');
    expect(context7Entry).toBeDefined();
    expect(context7Entry!.builtin).toBe(false);
    expect(context7Entry!.config).toEqual(customContext7Config);
  });

  it('does not inject builtin metadata into user-defined MCP servers', () => {
    const tools = [
      makeTool({
        config_content: JSON.stringify({
          mcpServers: {
            custom: { type: 'http', url: 'https://custom.example.com/mcp' },
          },
        }),
      }),
    ];

    const { configJson } = buildGitHubMcpConfig(tools);
    const parsed = JSON.parse(configJson) as {
      mcpServers: Record<string, { builtin?: boolean }>;
    };

    expect(parsed.mcpServers.custom.builtin).toBeUndefined();
    expect(parsed.mcpServers.context7.builtin).toBe(true);
  });

  it('deduplicates server keys across multiple tools', () => {
    const tools = [
      makeTool({
        id: 'tool-1',
        name: 'Tool A',
        config_content: JSON.stringify({
          mcpServers: {
            shared: { type: 'http', url: 'https://first.com' },
          },
        }),
      }),
      makeTool({
        id: 'tool-2',
        name: 'Tool B',
        config_content: JSON.stringify({
          mcpServers: {
            shared: { type: 'http', url: 'https://second.com' },
          },
        }),
      }),
    ];

    const { entries } = buildGitHubMcpConfig(tools);

    const sharedEntries = entries.filter((e) => e.key === 'shared');
    expect(sharedEntries).toHaveLength(1);
    // First tool wins
    expect(sharedEntries[0].config).toEqual({ type: 'http', url: 'https://first.com' });
  });

  it('produces valid JSON output', () => {
    const { configJson } = buildGitHubMcpConfig([]);
    expect(() => JSON.parse(configJson)).not.toThrow();
  });

  it('skips tools with malformed config_content', () => {
    const tools = [
      makeTool({
        id: 'tool-bad',
        name: 'Bad Tool',
        config_content: 'NOT VALID JSON',
      }),
      makeTool({
        id: 'tool-good',
        name: 'Good Tool',
        config_content: JSON.stringify({
          mcpServers: { good: { type: 'http', url: 'https://good.com' } },
        }),
      }),
    ];

    const { entries } = buildGitHubMcpConfig(tools);

    const userEntries = entries.filter((e) => !e.builtin);
    expect(userEntries).toHaveLength(1);
    expect(userEntries[0].key).toBe('good');
  });
});
