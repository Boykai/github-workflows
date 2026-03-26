/**
 * Regression tests for FilePreviewChips utility functions.
 */

import { describe, it, expect } from 'vitest';
import { truncateFilename } from './FilePreviewChips';

describe('truncateFilename', () => {
  it('returns short filenames unchanged', () => {
    expect(truncateFilename('short.txt')).toBe('short.txt');
  });

  it('truncates long filenames preserving extension', () => {
    const result = truncateFilename('very-long-filename-here.txt', 20);
    expect(result).toContain('.txt');
    expect(result).toContain('…');
    expect(result.length).toBeLessThanOrEqual(20);
  });

  it('truncates long filenames without extension', () => {
    const result = truncateFilename('a-very-long-filename-without-ext', 20);
    expect(result).toContain('…');
  });

  it('handles extension longer than max without negative slice', () => {
    // Regression: when extStr.length >= max, base slice index was negative
    const result = truncateFilename('file.verylongextensionname', 10);
    expect(result).toContain('…');
    expect(result).toContain('.verylongextensionname');
    // The base should have at least 1 character (Math.max(1, ...))
    expect(result.startsWith('f')).toBe(true);
  });

  it('handles extension longer than max length', () => {
    // Extension ".abcdefghij" is 11 chars while max is 10 (extension > max)
    const result = truncateFilename('x.abcdefghij', 10);
    expect(result).toContain('…');
    expect(result).toContain('.abcdefghij');
  });
});
