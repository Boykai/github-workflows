/**
 * Hook for command system integration.
 * Provides parsing, execution, and autocomplete filtering for # commands.
 */

import { useCallback } from 'react';
import { useTheme } from '@/components/ThemeProvider';
import { useUserSettings } from '@/hooks/useSettings';
import { parseCommand, getCommand, getAllCommands, filterCommands } from '@/lib/commands/registry';
import type { CommandContext, CommandResult, CommandDefinition } from '@/lib/commands/types';
import type { ChatMessage } from '@/types';

export interface UseCommandsReturn {
  /** Check if input is a command. */
  isCommand: (input: string) => boolean;
  /** Parse input into a ParsedCommand. */
  parseInput: (input: string) => ReturnType<typeof parseCommand>;
  /** Execute a command input and return the result. */
  executeCommand: (input: string) => CommandResult | Promise<CommandResult>;
  /** Get filtered commands for autocomplete. */
  getFilteredCommands: (prefix: string) => CommandDefinition[];
  /** Get all registered commands. */
  getAllCommands: () => CommandDefinition[];
}

export function useCommands(
  deps: { clearChat?: () => Promise<void>; messages?: ChatMessage[] } = {}
): UseCommandsReturn {
  const { theme, setTheme } = useTheme();
  const { settings, updateSettings } = useUserSettings();
  const { clearChat, messages } = deps;

  const buildContext = useCallback(
    (): CommandContext => ({
      setTheme: (t: string) => setTheme(t as 'light' | 'dark' | 'system'),
      updateSettings,
      currentSettings: settings,
      currentTheme: theme,
      clearChat: clearChat ?? (async () => {}),
      messages: messages ?? [],
    }),
    [theme, setTheme, settings, updateSettings, clearChat, messages]
  );

  const isCommandFn = useCallback((input: string): boolean => {
    return parseCommand(input).isCommand;
  }, []);

  const parseInput = useCallback((input: string) => {
    return parseCommand(input);
  }, []);

  const executeCommandFn = useCallback(
    (input: string): CommandResult | Promise<CommandResult> => {
      const parsed = parseCommand(input);

      if (!parsed.isCommand) {
        return { success: false, message: 'Not a command.', clearInput: false };
      }

      // Bare '/'
      if (!parsed.name) {
        return {
          success: false,
          message: 'Type /help to see available commands.',
          clearInput: false,
        };
      }

      const command = getCommand(parsed.name);
      if (!command) {
        return {
          success: false,
          message: `Unknown command '${parsed.name}'. Type /help to see available commands.`,
          clearInput: false,
        };
      }

      // Passthrough commands are handled by the backend — signal the caller
      // to forward the message to the API rather than displaying locally.
      if (command.passthrough) {
        return { success: true, message: '', clearInput: true, passthrough: true };
      }

      const context = buildContext();
      return command.handler(parsed.args, context);
    },
    [buildContext]
  );

  const getFilteredCommandsFn = useCallback((prefix: string): CommandDefinition[] => {
    return filterCommands(prefix);
  }, []);

  const getAllCommandsFn = useCallback((): CommandDefinition[] => {
    return getAllCommands();
  }, []);

  return {
    isCommand: isCommandFn,
    parseInput,
    executeCommand: executeCommandFn,
    getFilteredCommands: getFilteredCommandsFn,
    getAllCommands: getAllCommandsFn,
  };
}
