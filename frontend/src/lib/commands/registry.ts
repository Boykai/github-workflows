/**
 * Command registry — single source of truth for all # commands.
 *
 * All command surfaces (help output, autocomplete, execution) consume
 * this registry. Adding a new command here automatically makes it
 * available everywhere.
 */

import type { CommandDefinition, ParsedCommand } from './types';
import { helpHandler } from './handlers/help';
import { themeHandler, languageHandler, notificationsHandler, viewHandler } from './handlers/settings';

/** Central command store keyed by lowercase command name. */
const registry = new Map<string, CommandDefinition>();

/** Register a command definition. */
export function registerCommand(command: CommandDefinition): void {
  registry.set(command.name.toLowerCase(), command);
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
 * 1. Input starting with '#' (after trim) is a command.
 * 2. 'help' (exact, case-insensitive after trim) is a help alias.
 * 3. Command name is the first word after '#', lowercased.
 * 4. Arguments are everything after the command name, whitespace-normalized.
 * 5. Bare '#' results in isCommand:true with name:null.
 */
export function parseCommand(input: string): ParsedCommand {
  const trimmed = input.trim();
  const raw = input;

  // 'help' keyword alias (exact match, case-insensitive)
  if (trimmed.toLowerCase() === 'help') {
    return { isCommand: true, name: 'help', args: '', raw };
  }

  // Must start with '#'
  if (!trimmed.startsWith('#')) {
    return { isCommand: false, name: null, args: '', raw };
  }

  const afterHash = trimmed.slice(1).trim();

  // Bare '#'
  if (!afterHash) {
    return { isCommand: true, name: null, args: '', raw };
  }

  // Split into command name and arguments
  const spaceIndex = afterHash.indexOf(' ');
  if (spaceIndex === -1) {
    return { isCommand: true, name: afterHash.toLowerCase(), args: '', raw };
  }

  const name = afterHash.slice(0, spaceIndex).toLowerCase();
  const args = afterHash.slice(spaceIndex + 1).trim().replace(/\s+/g, ' ');

  return { isCommand: true, name, args, raw };
}

// ── Register built-in commands ─────────────────────────────────────────────

registerCommand({
  name: 'help',
  description: 'Show all available commands',
  syntax: '#help',
  handler: helpHandler,
});

registerCommand({
  name: 'theme',
  description: 'Change the UI theme',
  syntax: '#theme <light|dark|system>',
  handler: themeHandler,
  parameterSchema: { type: 'enum', values: ['light', 'dark', 'system'] },
});

registerCommand({
  name: 'language',
  description: 'Change the display language',
  syntax: '#language <en|es|fr|de|ja|zh>',
  handler: languageHandler,
  parameterSchema: { type: 'enum', values: ['en', 'es', 'fr', 'de', 'ja', 'zh'] },
});

registerCommand({
  name: 'notifications',
  description: 'Toggle notifications on or off',
  syntax: '#notifications <on|off>',
  handler: notificationsHandler,
  parameterSchema: { type: 'enum', values: ['on', 'off'] },
});

registerCommand({
  name: 'view',
  description: 'Set the default view',
  syntax: '#view <chat|board|settings>',
  handler: viewHandler,
  parameterSchema: { type: 'enum', values: ['chat', 'board', 'settings'] },
});
