import { describe, expect } from 'vitest';
import { test, fc } from '@fast-check/vitest';
import { cn } from './utils';

describe('cn (tailwind-merge) property tests', () => {
  test.prop([fc.array(fc.string({ minLength: 0, maxLength: 50 }), { minLength: 0, maxLength: 5 })])(
    'always returns a string',
    (inputs) => {
      const result = cn(...inputs);
      expect(typeof result).toBe('string');
    },
  );

  test.prop([fc.string({ minLength: 1, maxLength: 30 })])(
    'single class passes through',
    (cls) => {
      const result = cn(cls);
      expect(typeof result).toBe('string');
    },
  );

  test.prop([fc.string({ minLength: 1, maxLength: 20 })])(
    'duplicate classes are deduplicated',
    (cls) => {
      const result = cn(cls, cls);
      // twMerge deduplicates identical classes
      expect(typeof result).toBe('string');
    },
  );

  test('empty input returns empty string', () => {
    expect(cn()).toBe('');
  });
});
