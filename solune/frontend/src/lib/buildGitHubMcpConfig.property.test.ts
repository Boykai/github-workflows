import { describe } from 'vitest';
import { test, fc } from '@fast-check/vitest';
import { buildGitHubMcpConfig, extractServersFromTool, BUILTIN_MCPS } from './buildGitHubMcpConfig';
import type { McpToolConfig } from '@/types';

function makeTool(overrides: Partial<McpToolConfig> = {}): McpToolConfig {
  return {
    id: 'tool-1',
    github_user_id: 'u1',
    project_id: 'p1',
    name: 'Test Tool',
    description: 'desc',
    endpoint_url: '',
    config_content: JSON.stringify({ mcpServers: { myServer: { type: 'http', url: 'http://localhost' } } }),
    sync_status: 'synced',
    sync_error: null,
    synced_at: null,
    github_repo_target: 'owner/repo',
    is_active: true,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    ...overrides,
  };
}

describe('buildGitHubMcpConfig property tests', () => {
  test.prop([fc.array(fc.string(), { minLength: 0, maxLength: 5 })])(
    'output always includes all built-in MCP keys when no user tools conflict',
    (serverNames) => {
      // Tools with arbitrary names that don't conflict with built-in keys
      const tools = serverNames.map((name, i) =>
        makeTool({
          id: `tool-${i}`,
          name: `Tool ${i}`,
          config_content: JSON.stringify({
            mcpServers: { [`user_${name}_${i}`]: { type: 'http', url: 'http://test' } },
          }),
        }),
      );

      const { entries } = buildGitHubMcpConfig(tools);
      const keys = entries.map((e) => e.key);

      for (const builtin of BUILTIN_MCPS) {
        expect(keys).toContain(builtin.serverKey);
      }
    },
  );

  test.prop([fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 0, maxLength: 10 })])(
    'output JSON is always valid and parseable',
    (names) => {
      const tools = names.map((name, i) =>
        makeTool({
          id: `tool-${i}`,
          name: `Tool ${i}`,
          config_content: JSON.stringify({
            mcpServers: { [`srv_${i}`]: { type: 'http', url: 'http://test' } },
          }),
        }),
      );

      const { configJson } = buildGitHubMcpConfig(tools);
      const parsed = JSON.parse(configJson);
      expect(parsed).toHaveProperty('mcpServers');
      expect(typeof parsed.mcpServers).toBe('object');
    },
  );

  test.prop([fc.string()])(
    'extractServersFromTool returns empty array for malformed JSON',
    (badContent) => {
      const tool = makeTool({ config_content: badContent });
      const result = extractServersFromTool(tool);
      expect(Array.isArray(result)).toBe(true);
    },
  );

  test.prop([fc.array(fc.string({ minLength: 1, maxLength: 10 }), { minLength: 1, maxLength: 5 })])(
    'no duplicate keys in output entries',
    (serverKeys) => {
      const tools = serverKeys.map((key, i) =>
        makeTool({
          id: `tool-${i}`,
          name: `Tool ${i}`,
          config_content: JSON.stringify({
            mcpServers: { [key]: { type: 'http', url: 'http://test' } },
          }),
        }),
      );

      const { entries } = buildGitHubMcpConfig(tools);
      const keys = entries.map((e) => e.key);
      expect(new Set(keys).size).toBe(keys.length);
    },
  );
});
