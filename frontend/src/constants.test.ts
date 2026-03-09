/**
 * Unit tests for BREAKPOINTS constant.
 */
import { describe, it, expect } from 'vitest';
import { BREAKPOINTS } from './constants';

describe('BREAKPOINTS', () => {
  it('defines all expected responsive breakpoints', () => {
    expect(BREAKPOINTS).toEqual({
      xs: 320,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
      '2xl': 1440,
    });
  });

  it('has breakpoints in ascending order', () => {
    const values = Object.values(BREAKPOINTS);
    for (let i = 1; i < values.length; i++) {
      expect(values[i]).toBeGreaterThan(values[i - 1]);
    }
  });
});
