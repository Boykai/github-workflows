/**
 * Handler for the /help command.
 */

import type { CommandResult, CommandContext } from '../types';
import { getAllCommands } from '../registry';

export function helpHandler(_args: string, _context: CommandContext): CommandResult {
  const commands = getAllCommands();
  const lines = commands.map((cmd) => `  ${cmd.syntax}  —  ${cmd.description}`);
  // Use plain text formatting since chat messages are rendered without
  // a Markdown parser — literal ** markers would be shown to the user.
  const message = `Available Commands:\n${lines.join('\n')}`;
  return { success: true, message, clearInput: true };
}
