import { describe, expect } from 'vitest';
import { test, fc } from '@fast-check/vitest';
import {
  daysToMs,
  formatMsRemaining,
  formatMsAgo,
  computeCountRemaining,
  computeCountProgress,
  MS_PER_DAY,
} from './time-utils';

describe('time-utils property tests', () => {
  test.prop([fc.integer({ min: 0, max: 10000 })])(
    'daysToMs is inverse of dividing by MS_PER_DAY',
    (days) => {
      expect(daysToMs(days)).toBe(days * MS_PER_DAY);
      expect(daysToMs(days) / MS_PER_DAY).toBe(days);
    },
  );

  test.prop([fc.integer({ min: 1, max: 10_000_000_000 })])(
    'formatMsRemaining never returns empty string for positive values',
    (ms) => {
      const result = formatMsRemaining(ms);
      expect(result.length).toBeGreaterThan(0);
      expect(result).toContain('remaining');
    },
  );

  test.prop([fc.integer({ min: -1_000_000, max: 0 })])(
    'formatMsRemaining returns "Due now" for zero or negative',
    (ms) => {
      expect(formatMsRemaining(ms)).toBe('Due now');
    },
  );

  test.prop([fc.integer({ min: 0, max: 10_000_000_000 })])(
    'formatMsAgo never returns empty string',
    (ms) => {
      const result = formatMsAgo(ms);
      expect(result.length).toBeGreaterThan(0);
      expect(result).toMatch(/^Run /);
    },
  );

  test.prop([
    fc.integer({ min: 1, max: 1000 }),
    fc.integer({ min: 0, max: 10000 }),
    fc.integer({ min: 0, max: 10000 }),
  ])(
    'computeCountRemaining is non-negative',
    (scheduleValue, parentIssueCount, lastTriggeredCount) => {
      const result = computeCountRemaining(scheduleValue, parentIssueCount, lastTriggeredCount);
      expect(result).toBeGreaterThanOrEqual(0);
    },
  );

  test.prop([
    fc.integer({ min: 1, max: 1000 }),
    fc.integer({ min: 0, max: 1000 }),
  ])(
    'computeCountProgress is between 0 and 1 when remaining <= scheduleValue',
    (scheduleValue, remaining) => {
      fc.pre(remaining <= scheduleValue);
      const result = computeCountProgress(scheduleValue, remaining);
      expect(result).toBeGreaterThanOrEqual(0);
      expect(result).toBeLessThanOrEqual(1);
    },
  );

  test.prop([fc.integer({ min: 0, max: 1000 })])(
    'computeCountProgress returns 0 when scheduleValue is 0',
    (remaining) => {
      expect(computeCountProgress(0, remaining)).toBe(0);
    },
  );
});
