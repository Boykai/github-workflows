/**
 * Handler stub for the #agent command.
 *
 * The actual agent-creation logic lives on the backend (agent_creator service).
 * This handler is only invoked as a fallback — normally the passthrough flag
 * on the CommandDefinition causes useChat to forward the message to the API
 * instead of executing this handler locally.
 */

import type { CommandResult } from '../types';

export function agentHandler(): CommandResult {
  return {
    success: true,
    message: '',
    clearInput: true,
    passthrough: true,
  };
}
