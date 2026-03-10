/**
 * Case-insensitive object key utilities.
 *
 * Replaces repeated `Object.keys(obj).find(k => k.toLowerCase() === …)`
 * patterns with a single reusable helper.
 */

/**
 * Find a key in `obj` that matches `key` case-insensitively.
 *
 * Returns the **original** (correctly-cased) key from the object if found,
 * or falls back to the provided `key` when no match exists.
 */
export function caseInsensitiveKey<T extends Record<string, unknown>>(
  obj: T,
  key: string,
): string {
  const lower = key.toLowerCase();
  return Object.keys(obj).find((k) => k.toLowerCase() === lower) ?? key;
}
