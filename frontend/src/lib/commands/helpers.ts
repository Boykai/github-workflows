/**
 * Helper utilities for the chat command system.
 * Provides fuzzy matching and input sanitization for error messages.
 */

import { getAllCommands } from './registry';
import type { CommandDefinition } from './types';

/**
 * Compute the Levenshtein edit distance between two strings.
 * Used for "Did you mean?" suggestions on unknown commands.
 */
export function levenshteinDistance(a: string, b: string): number {
  const m = a.length;
  const n = b.length;

  // Create a 2D matrix for dynamic programming
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0) as number[]);

  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,      // deletion
        dp[i][j - 1] + 1,      // insertion
        dp[i - 1][j - 1] + cost // substitution
      );
    }
  }

  return dp[m][n];
}

/**
 * Find registered commands whose names are within `maxDistance` edits
 * of the given input. Returns matches sorted by distance (closest first).
 */
export function findClosestCommands(input: string, maxDistance: number = 2): CommandDefinition[] {
  const lower = input.toLowerCase();
  const commands = getAllCommands();

  const matches: Array<{ command: CommandDefinition; distance: number }> = [];

  for (const cmd of commands) {
    const distance = levenshteinDistance(lower, cmd.name);
    if (distance > 0 && distance <= maxDistance) {
      matches.push({ command: cmd, distance });
    }
  }

  matches.sort((a, b) => a.distance - b.distance);
  return matches.map((m) => m.command);
}

/**
 * Truncate user input for display in error messages.
 * Prevents layout breakage from very long strings.
 */
export function truncateInput(input: string, maxLength: number = 50): string {
  if (input.length <= maxLength) return input;
  return input.slice(0, maxLength) + '...';
}
