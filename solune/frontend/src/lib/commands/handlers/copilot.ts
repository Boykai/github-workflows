/**
 * Handler stub for Copilot passthrough commands.
 *
 * The actual Copilot command logic lives on the backend (copilot_commands service).
 * This handler is only invoked as a fallback — normally the passthrough flag
 * on the CommandDefinition causes useChat to forward the message to the API
 * instead of executing this handler locally.
 */

import type { CommandResult } from '../types';

export function copilotPassthroughHandler(): CommandResult {
  return {
    success: true,
    message: '',
    clearInput: true,
    passthrough: true,
  };
}
