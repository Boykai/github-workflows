/**
 * Type definitions for the chat command system.
 */

import type { ChatMessage, EffectiveUserSettings, UserPreferencesUpdate } from '@/types';

/** Valid parameter definition for commands that accept arguments. */
export interface ParameterSchema {
  type: 'enum' | 'string' | 'boolean';
  values?: string[];
  labels?: Record<string, string>;
}

/** Runtime context passed to command handlers. */
export interface CommandContext {
  setTheme: (theme: string) => void;
  updateSettings: (data: UserPreferencesUpdate) => Promise<unknown>;
  currentSettings: EffectiveUserSettings | undefined;
  currentTheme: string;
  clearChat: () => Promise<void>;
  messages: ChatMessage[];
}

/** Result of executing a command handler. */
export interface CommandResult {
  success: boolean;
  message: string;
  clearInput: boolean;
  /** When true, the message should be forwarded to the backend instead of displayed locally. */
  passthrough?: boolean;
}

/** Handler function signature for commands. */
export type CommandHandler = (
  args: string,
  context: CommandContext
) => CommandResult | Promise<CommandResult>;

/** A single entry in the command registry. */
export interface CommandDefinition {
  name: string;
  description: string;
  syntax: string;
  handler: CommandHandler;
  parameterSchema?: ParameterSchema;
  /** When true, the command is handled by the backend. The frontend shows it in
   *  #help / autocomplete but forwards the message to the API instead of
   *  executing the handler locally. */
  passthrough?: boolean;
}

/** Result of parsing a user's chat input. */
export interface ParsedCommand {
  isCommand: boolean;
  name: string | null;
  args: string;
  raw: string;
}
