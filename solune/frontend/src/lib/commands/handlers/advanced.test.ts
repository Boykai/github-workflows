/**
 * Unit tests for advanced command handlers (/model, /mcp, /plan).
 */
import { describe, it, expect } from 'vitest';
import { modelHandler, mcpHandler, planHandler } from './advanced';

describe('modelHandler', () => {
  it('returns passthrough result', () => {
    const result = modelHandler();

    expect(result.success).toBe(true);
    expect(result.passthrough).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toBe('');
  });
});

describe('mcpHandler', () => {
  it('returns passthrough result', () => {
    const result = mcpHandler();

    expect(result.success).toBe(true);
    expect(result.passthrough).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toBe('');
  });
});

describe('planHandler', () => {
  it('returns passthrough result', () => {
    const result = planHandler();

    expect(result.success).toBe(true);
    expect(result.passthrough).toBe(true);
    expect(result.clearInput).toBe(true);
    expect(result.message).toBe('');
  });
});
