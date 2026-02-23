/**
 * Generate a unique ID string.
 *
 * Uses `crypto.randomUUID()` when available (all modern browsers),
 * falling back to a Math.random + Date.now combination.
 */
export function generateId(): string {
  return globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2) + Date.now().toString(36);
}
