import { describe, expect } from 'vitest';
import { test, fc } from '@fast-check/vitest';
import { caseInsensitiveKey } from './case-utils';

describe('caseInsensitiveKey property tests', () => {
  test.prop([
    fc.dictionary(fc.string({ minLength: 1, maxLength: 20 }), fc.anything()),
    fc.string({ minLength: 1, maxLength: 20 }),
  ])(
    'always returns a string',
    (obj, key) => {
      const result = caseInsensitiveKey(obj, key);
      expect(typeof result).toBe('string');
    },
  );

  test.prop([
    fc.dictionary(fc.string({ minLength: 1, maxLength: 20 }), fc.constant(1), { minKeys: 1 }),
  ])(
    'finds existing key regardless of case',
    (obj) => {
      const existingKey = Object.keys(obj)[0];
      // Search with upper-cased version
      const result = caseInsensitiveKey(obj, existingKey.toUpperCase());
      // Should find the original key
      expect(result.toLowerCase()).toBe(existingKey.toLowerCase());
      // And that key must actually exist in the object
      expect(obj).toHaveProperty(result);
    },
  );

  test.prop([fc.string({ minLength: 1, maxLength: 20 })])(
    'returns key itself when object is empty',
    (key) => {
      const result = caseInsensitiveKey({}, key);
      expect(result).toBe(key);
    },
  );

  test.prop([
    fc.string({ minLength: 1, maxLength: 10 }),
    fc.anything(),
  ])(
    'exact match always returns the key',
    (key, value) => {
      const obj = { [key]: value };
      const result = caseInsensitiveKey(obj, key);
      expect(result).toBe(key);
    },
  );
});
