/**
 * Tests for useSecrets hooks — query key structure and hook behavior.
 */

import { describe, it, expect } from 'vitest';
import { secretsKeys } from './useSecrets';

describe('secretsKeys', () => {
  it('all returns base key', () => {
    expect(secretsKeys.all).toEqual(['secrets']);
  });

  it('list returns key with owner, repo, env', () => {
    const key = secretsKeys.list('owner1', 'my-repo', 'copilot');
    expect(key).toEqual(['secrets', 'list', 'owner1', 'my-repo', 'copilot']);
  });

  it('check returns key with owner, repo, env, and secret names', () => {
    const key = secretsKeys.check('owner1', 'my-repo', 'copilot', ['SECRET_A', 'SECRET_B']);
    expect(key).toEqual([
      'secrets',
      'check',
      'owner1',
      'my-repo',
      'copilot',
      'SECRET_A',
      'SECRET_B',
    ]);
  });

  it('list keys with different params are distinct', () => {
    const key1 = secretsKeys.list('owner1', 'repo-a', 'copilot');
    const key2 = secretsKeys.list('owner1', 'repo-b', 'copilot');
    expect(key1).not.toEqual(key2);
  });

  it('all list keys start with the base key', () => {
    const key = secretsKeys.list('o', 'r', 'e');
    expect(key[0]).toBe('secrets');
  });
});
