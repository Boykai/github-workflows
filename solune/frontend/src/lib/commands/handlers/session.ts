/**
 * Handlers for session management commands (/clear, /compact, /context).
 */

import type { CommandResult, CommandContext } from '../types';

// ── /clear ──────────────────────────────────────────────────────────────────

export async function clearHandler(_args: string, context: CommandContext): Promise<CommandResult> {
  if (context.messages.length === 0) {
    return {
      success: true,
      message: 'No messages to clear.',
      clearInput: true,
    };
  }

  try {
    await context.clearChat();
  } catch {
    return {
      success: false,
      message: 'Failed to clear chat. Please try again.',
      clearInput: false,
    };
  }

  return {
    success: true,
    message: '🗑️ Chat cleared.',
    clearInput: true,
  };
}

// ── /compact ────────────────────────────────────────────────────────────────

export function compactHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}

// ── /context ────────────────────────────────────────────────────────────────

export function contextHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}
