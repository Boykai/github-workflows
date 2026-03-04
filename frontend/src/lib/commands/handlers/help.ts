/**
 * Handler for the #help command.
 */

import type { CommandResult, CommandContext } from '../types';
import { getCommand, getCommandsByCategory } from '../registry';

export function helpHandler(args: string, _context: CommandContext): CommandResult {
  const query = args.trim();

  // Single-command help: #help <command>
  if (query) {
    // Strip leading # to handle "#help #theme"
    const commandName = query.startsWith('#') ? query.slice(1) : query;
    const command = getCommand(commandName);

    if (!command) {
      return {
        success: false,
        message: `Command '${commandName}' not found.\nType #help to see all available commands.`,
        clearInput: true,
      };
    }

    // Build detailed single-command help
    const lines: string[] = [
      `#${command.name}  —  ${command.description}`,
      '',
      `Usage: ${command.syntax}`,
    ];

    if (command.parameterSchema?.values) {
      lines.push(`Options: ${command.parameterSchema.values.join(', ')}`);
    }

    // Add example
    if (command.parameterSchema?.values) {
      lines.push('', `Example: #${command.name} ${command.parameterSchema.values[0]}`);
    }

    return { success: true, message: lines.join('\n'), clearInput: true };
  }

  // Full categorized help listing
  const categories = getCommandsByCategory();

  if (categories.length === 0) {
    return { success: true, message: 'No commands available.', clearInput: true };
  }

  // Use plain text formatting since chat messages are rendered without
  // a Markdown parser — literal ** markers would be shown to the user.
  const sections = categories.map(({ category, commands }) => {
    const cmdLines = commands.map((cmd) => `  ${cmd.syntax}  —  ${cmd.description}`);
    return `${category}\n${cmdLines.join('\n')}`;
  });

  const message = `Available Commands:\n\n${sections.join('\n\n')}`;
  return { success: true, message, clearInput: true };
}
