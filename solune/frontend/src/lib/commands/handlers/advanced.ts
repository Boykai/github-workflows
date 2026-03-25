/**
 * Handlers for advanced configuration commands (/model, /mcp, /plan).
 */

import type { CommandResult } from '../types';

// ── /model ──────────────────────────────────────────────────────────────────

export function modelHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}

// ── /mcp ────────────────────────────────────────────────────────────────────

export function mcpHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}

// ── /plan ───────────────────────────────────────────────────────────────────

export function planHandler(): CommandResult {
  return { success: true, message: '', clearInput: true, passthrough: true };
}
