/**
 * buildGitHubMcpConfig — generates a GitHub.com MCP configuration block
 * from a user's active project tools plus built-in MCPs.
 *
 * The output format conforms to the GitHub.com remote Custom GitHub Agents
 * MCP configuration schema (mcpServers JSON object).
 */

import type { McpToolConfig } from '@/types';

/* ── Built-in MCP definitions ───────────────────────────────────────── */

export interface BuiltInMcp {
  /** Display name shown in the UI */
  name: string;
  /** Key used inside the mcpServers object */
  serverKey: string;
  /** The MCP server configuration object */
  config: Record<string, unknown>;
}

export const BUILTIN_MCPS: readonly BuiltInMcp[] = [
  {
    name: 'Context7',
    serverKey: 'context7',
    config: {
      builtin: true,
      type: 'http',
      url: 'https://mcp.context7.com/mcp',
      tools: ['resolve-library-id', 'get-library-docs'],
      headers: {
        CONTEXT7_API_KEY: '$COPILOT_MCP_CONTEXT7_API_KEY',
      },
    },
  },
  {
    name: 'Code Graph Context',
    serverKey: 'CodeGraphContext',
    config: {
      builtin: true,
      type: 'local',
      command: 'uvx',
      args: ['--from', 'codegraphcontext', 'cgc', 'mcp', 'start'],
      tools: ['*'],
    },
  },
] as const;

/* ── Config builder ─────────────────────────────────────────────────── */

export interface McpServerEntry {
  key: string;
  config: Record<string, unknown>;
  builtin: boolean;
  sourceName: string;
}

/**
 * Extracts individual MCP server entries from a tool's config_content JSON.
 * Returns an empty array if the config is malformed.
 */
export function extractServersFromTool(tool: McpToolConfig): McpServerEntry[] {
  try {
    const parsed = JSON.parse(tool.config_content) as {
      mcpServers?: Record<string, Record<string, unknown>>;
    };
    const mcpServers = parsed.mcpServers;
    if (!mcpServers || typeof mcpServers !== 'object' || Array.isArray(mcpServers)) return [];

    const entries: McpServerEntry[] = [];
    for (const [key, config] of Object.entries(mcpServers)) {
      if (!config || typeof config !== 'object' || Array.isArray(config)) continue;
      entries.push({ key, config: config as Record<string, unknown>, builtin: false, sourceName: tool.name });
    }
    return entries;
  } catch {
    return [];
  }
}

/**
 * Builds the merged GitHub.com MCP configuration JSON from the user's
 * active project tools and built-in MCPs.
 *
 * Built-in MCPs are always included. If a user tool defines a server with
 * the same key as a built-in, the user's version takes precedence.
 */
export function buildGitHubMcpConfig(tools: McpToolConfig[]): {
  configJson: string;
  entries: McpServerEntry[];
} {
  const entries: McpServerEntry[] = [];
  const seenKeys = new Set<string>();

  // 1. Add all user tool servers first
  for (const tool of tools) {
    for (const entry of extractServersFromTool(tool)) {
      if (!seenKeys.has(entry.key)) {
        seenKeys.add(entry.key);
        entries.push(entry);
      }
    }
  }

  // 2. Add built-in MCPs (only if not already overridden by user tools)
  for (const builtin of BUILTIN_MCPS) {
    if (!seenKeys.has(builtin.serverKey)) {
      seenKeys.add(builtin.serverKey);
      entries.push({
        key: builtin.serverKey,
        config: builtin.config,
        builtin: true,
        sourceName: builtin.name,
      });
    }
  }

  // 3. Build the mcpServers object (null-prototype to avoid prototype pollution)
  const mcpServers = Object.create(null) as Record<string, Record<string, unknown>>;
  for (const entry of entries) {
    mcpServers[entry.key] = entry.config;
  }

  const configJson = JSON.stringify({ mcpServers }, null, 2);

  return { configJson, entries };
}
