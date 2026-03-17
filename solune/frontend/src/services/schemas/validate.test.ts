import { describe, it, expect, vi, beforeEach } from 'vitest';
import { z } from 'zod';
import { validateResponse } from './validate';

const TestSchema = z.object({ name: z.string(), value: z.number() });

describe('validateResponse', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('returns valid data successfully', () => {
    const data = { name: 'test', value: 42 };
    const result = validateResponse(TestSchema, data, 'test-endpoint');
    expect(result).toEqual(data);
  });

  it('parses and returns correct field values', () => {
    const data = { name: 'test', value: 42 };
    const result = validateResponse(TestSchema, data, 'test-endpoint');
    expect(result.name).toBe('test');
    expect(result.value).toBe(42);
  });

  it('throws and logs on invalid data in dev mode', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const invalidData = { name: 123 };

    expect(() => validateResponse(TestSchema, invalidData, 'test-endpoint')).toThrow();
    expect(consoleSpy).toHaveBeenCalledWith(
      '[API Schema Validation] test-endpoint:',
      expect.any(Error)
    );
  });

  it('works with complex schema types', () => {
    const ComplexSchema = z.object({
      items: z.array(z.object({ id: z.string() })),
    });
    const data = { items: [{ id: 'a' }, { id: 'b' }] };
    const result = validateResponse(ComplexSchema, data, 'complex-endpoint');
    expect(result.items).toHaveLength(2);
  });

  it('strips extra fields via schema parse in dev mode', () => {
    const data = { name: 'test', value: 42, extra: 'ignored' };
    const result = validateResponse(TestSchema, data, 'test-endpoint');
    expect(result).toEqual({ name: 'test', value: 42 });
  });
});
