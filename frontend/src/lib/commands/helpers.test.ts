/**
 * Unit tests for command helper utilities.
 */
import { describe, it, expect } from 'vitest';
import { levenshteinDistance, findClosestCommands, truncateInput } from './helpers';

describe('levenshteinDistance', () => {
  it('returns 0 for identical strings', () => {
    expect(levenshteinDistance('help', 'help')).toBe(0);
  });

  it('returns 1 for single insertion', () => {
    expect(levenshteinDistance('hep', 'help')).toBe(1);
  });

  it('returns 1 for single deletion', () => {
    expect(levenshteinDistance('helps', 'help')).toBe(1);
  });

  it('returns 1 for single substitution', () => {
    expect(levenshteinDistance('halp', 'help')).toBe(1);
  });

  it('returns 2 for transposition', () => {
    // 'hlep' -> 'help' requires 2 substitutions (l↔e swap)
    expect(levenshteinDistance('hlep', 'help')).toBe(2);
  });

  it('returns length for completely different strings', () => {
    expect(levenshteinDistance('abc', 'xyz')).toBe(3);
  });

  it('handles empty strings', () => {
    expect(levenshteinDistance('', 'help')).toBe(4);
    expect(levenshteinDistance('help', '')).toBe(4);
    expect(levenshteinDistance('', '')).toBe(0);
  });
});

describe('findClosestCommands', () => {
  it('returns closest matches within maxDistance threshold', () => {
    const matches = findClosestCommands('hep', 2);
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(matches[0].name).toBe('help');
  });

  it('returns empty array when no matches within threshold', () => {
    const matches = findClosestCommands('zzzzzzz', 2);
    expect(matches).toEqual([]);
  });

  it('returns matches sorted by distance (closest first)', () => {
    // 'vie' is distance 1 from 'view', distance 2+ from others
    const matches = findClosestCommands('vie', 2);
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(matches[0].name).toBe('view');
  });

  it('uses default maxDistance of 2', () => {
    const matches = findClosestCommands('hep');
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(matches[0].name).toBe('help');
  });

  it('does not return exact matches (distance 0)', () => {
    const matches = findClosestCommands('help', 2);
    // 'help' is distance 0 from 'help' — should not be returned
    const helpMatch = matches.find((m) => m.name === 'help');
    expect(helpMatch).toBeUndefined();
  });
});

describe('truncateInput', () => {
  it('returns short input unchanged', () => {
    expect(truncateInput('hello')).toBe('hello');
  });

  it('truncates input longer than maxLength with ellipsis', () => {
    const long = 'a'.repeat(60);
    const result = truncateInput(long);
    expect(result.length).toBe(53); // 50 + '...'
    expect(result.endsWith('...')).toBe(true);
  });

  it('uses default maxLength of 50', () => {
    const exactly50 = 'a'.repeat(50);
    expect(truncateInput(exactly50)).toBe(exactly50);

    const over50 = 'a'.repeat(51);
    expect(truncateInput(over50)).toContain('...');
  });

  it('supports custom maxLength', () => {
    expect(truncateInput('hello world', 5)).toBe('hello...');
    expect(truncateInput('hi', 5)).toBe('hi');
  });
});
