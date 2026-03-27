/**
 * Command registry — single source of truth for all /commands.
 *
 * All command surfaces (help output, autocomplete, execution) consume
 * this registry. Adding a new command here automatically makes it
 * available everywhere.
 */

import type { CommandDefinition, ParsedCommand } from './types';
import { helpHandler } from './handlers/help';
import {
  themeHandler,
  languageHandler,
  notificationsHandler,
  viewHandler,
  experimentalHandler,
} from './handlers/settings';
import { agentHandler } from './handlers/agent';
import { copilotPassthroughHandler } from './handlers/copilot';
import { clearHandler, compactHandler, contextHandler } from './handlers/session';
import { diffHandler, usageHandler, shareHandler, feedbackHandler } from './handlers/monitoring';
import { modelHandler, mcpHandler, planHandler } from './handlers/advanced';

/** Central command store keyed by lowercase command name. */
const registry = new Map<string, CommandDefinition>();

/** Register a command definition. */
export function registerCommand(command: CommandDefinition): void {
  registry.set(command.name.toLowerCase(), command);
}

/** Remove a command from the registry (useful for test teardown). */
export function unregisterCommand(name: string): void {
  registry.delete(name.toLowerCase());
}

/** Look up a command by name (case-insensitive). */
export function getCommand(name: string): CommandDefinition | undefined {
  return registry.get(name.toLowerCase());
}

/** Return all registered commands sorted alphabetically by name. */
export function getAllCommands(): CommandDefinition[] {
  return Array.from(registry.values()).sort((a, b) => a.name.localeCompare(b.name));
}

/** Return commands whose names start with the given prefix (case-insensitive). */
export function filterCommands(prefix: string): CommandDefinition[] {
  const lower = prefix.toLowerCase();
  return getAllCommands().filter((cmd) => cmd.name.startsWith(lower));
}

/**
 * Parse user input into a ParsedCommand.
 *
 * Rules:
 * 1. Input starting with '/' (after trim) is a command.
 * 2. 'help' (exact, case-insensitive after trim) is a help alias.
 * 3. Command name is the first word after '/', lowercased.
 * 4. Arguments are everything after the command name, whitespace-normalized.
 * 5. Bare '/' results in isCommand:true with name:null.
 *
 * Markdown characters (#, *, -, `, >) are NOT treated as commands.
 */
export function parseCommand(input: string): ParsedCommand {
  const trimmed = input.trim();
  const raw = input;

  // 'help' keyword alias (exact match, case-insensitive)
  if (trimmed.toLowerCase() === 'help') {
    return { isCommand: true, name: 'help', args: '', raw };
  }

  // Must start with '/'
  if (!trimmed.startsWith('/')) {
    return { isCommand: false, name: null, args: '', raw };
  }

  const afterSlash = trimmed.slice(1).trim();

  // Bare '/'
  if (!afterSlash) {
    return { isCommand: true, name: null, args: '', raw };
  }

  // Split into command name and arguments
  const spaceIndex = afterSlash.indexOf(' ');
  if (spaceIndex === -1) {
    return { isCommand: true, name: afterSlash.toLowerCase(), args: '', raw };
  }

  const name = afterSlash.slice(0, spaceIndex).toLowerCase();
  const args = afterSlash
    .slice(spaceIndex + 1)
    .trim()
    .replace(/\s+/g, ' ');

  return { isCommand: true, name, args, raw };
}

// ── Register built-in commands ─────────────────────────────────────────────

registerCommand({
  name: 'help',
  description: 'Show all available commands',
  syntax: '/help',
  handler: helpHandler,
  category: 'solune',
});

registerCommand({
  name: 'theme',
  description: 'Change the UI theme',
  syntax: '/theme <light|dark|system>',
  handler: themeHandler,
  parameterSchema: { type: 'enum', values: ['light', 'dark', 'system'] },
  category: 'solune',
});

registerCommand({
  name: 'language',
  description: 'Change the display language',
  syntax: '/language <en|es|fr|de|ja|zh>',
  handler: languageHandler,
  parameterSchema: { type: 'enum', values: ['en', 'es', 'fr', 'de', 'ja', 'zh'] },
  category: 'solune',
});

registerCommand({
  name: 'notifications',
  description: 'Toggle notifications on or off',
  syntax: '/notifications <on|off>',
  handler: notificationsHandler,
  parameterSchema: { type: 'enum', values: ['on', 'off'] },
  category: 'solune',
});

registerCommand({
  name: 'view',
  description: 'Set the default view',
  syntax: '/view <chat|board|settings>',
  handler: viewHandler,
  parameterSchema: { type: 'enum', values: ['chat', 'board', 'settings'] },
  category: 'solune',
});

registerCommand({
  name: 'agent',
  description: 'Create a custom agent for your project (admin only)',
  syntax: '/agent <description> [#status-column]',
  handler: agentHandler,
  passthrough: true,
  category: 'solune',
});

// ── Session commands ───────────────────────────────────────────────────────

registerCommand({
  name: 'clear',
  description: 'Clear all chat messages',
  syntax: '/clear',
  handler: clearHandler,
  category: 'solune',
});

registerCommand({
  name: 'compact',
  description: 'Summarize conversation to reduce context',
  syntax: '/compact',
  handler: compactHandler,
  passthrough: true,
  category: 'solune',
});

registerCommand({
  name: 'context',
  description: 'Show session statistics',
  syntax: '/context',
  handler: contextHandler,
  passthrough: true,
  category: 'solune',
});

// ── Advanced commands ──────────────────────────────────────────────────────

registerCommand({
  name: 'model',
  description: 'Show or switch the AI model',
  syntax: '/model [MODEL]',
  handler: modelHandler,
  passthrough: true,
  category: 'solune',
});

registerCommand({
  name: 'experimental',
  description: 'Toggle experimental features on or off',
  syntax: '/experimental [on|off]',
  handler: experimentalHandler,
  category: 'solune',
});

// ── Monitoring commands ────────────────────────────────────────────────────

registerCommand({
  name: 'diff',
  description: 'Show recent task/issue changes in session',
  syntax: '/diff',
  handler: diffHandler,
  passthrough: true,
  category: 'solune',
});

registerCommand({
  name: 'usage',
  description: 'Display session metrics',
  syntax: '/usage',
  handler: usageHandler,
  passthrough: true,
  category: 'solune',
});

registerCommand({
  name: 'share',
  description: 'Export chat as Markdown download',
  syntax: '/share',
  handler: shareHandler,
  category: 'solune',
});

registerCommand({
  name: 'feedback',
  description: 'Display feedback link',
  syntax: '/feedback',
  handler: feedbackHandler,
  category: 'solune',
});

// ── Power-user commands ────────────────────────────────────────────────────

registerCommand({
  name: 'mcp',
  description: 'Manage MCP configurations',
  syntax: '/mcp [show|add|delete]',
  handler: mcpHandler,
  passthrough: true,
  category: 'solune',
});

registerCommand({
  name: 'plan',
  description: 'Create or view an execution plan',
  syntax: '/plan [description]',
  handler: planHandler,
  passthrough: true,
  category: 'solune',
});

// ── GitHub Copilot commands ────────────────────────────────────────────────

registerCommand({
  name: 'explain',
  description: 'Explain code or concepts with examples',
  syntax: '/explain <code or concept>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'fix',
  description: 'Identify issues and provide corrected code',
  syntax: '/fix <code or error>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'doc',
  description: 'Generate documentation comments for code',
  syntax: '/doc <code>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'tests',
  description: 'Generate comprehensive unit tests',
  syntax: '/tests <code or function>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'setuptests',
  description: 'Recommend test framework and setup steps',
  syntax: '/setuptests <project type>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'new',
  description: 'Generate a new project scaffold',
  syntax: '/new <project description>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'newnotebook',
  description: 'Generate a Jupyter notebook outline',
  syntax: '/newnotebook <topic>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'search',
  description: 'Generate effective code search queries',
  syntax: '/search <what to find>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});

registerCommand({
  name: 'startdebugging',
  description: 'Generate debug launch configuration',
  syntax: '/startdebugging <project setup>',
  handler: copilotPassthroughHandler,
  passthrough: true,
  category: 'copilot',
});
