import { afterEach, beforeEach, describe, expect, vi } from 'vitest';
import { test, fc } from '@fast-check/vitest';

import { formatTimeAgo, formatTimeUntil } from './formatTime';

describe('formatTime property tests', () => {
  const fixedNow = new Date('2026-03-16T12:00:00.000Z');
  let timeStringSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(fixedNow);
    timeStringSpy = vi
      .spyOn(Date.prototype, 'toLocaleTimeString')
      .mockReturnValue('12:34:56 PM');
  });

  afterEach(() => {
    timeStringSpy.mockRestore();
    vi.useRealTimers();
  });

  it('formatTimeAgo uses exact boundaries for seconds, minutes, and fallback time', () => {
    expect(formatTimeAgo(new Date(fixedNow.getTime() - 59_000))).toBe('just now');
    expect(formatTimeAgo(new Date(fixedNow.getTime() - 60_000))).toBe('1m ago');
    expect(formatTimeAgo(new Date(fixedNow.getTime() - 3_599_000))).toBe('59m ago');
    expect(formatTimeAgo(new Date(fixedNow.getTime() - 3_600_000))).toBe('12:34:56 PM');
  });

  it('formatTimeUntil uses exact boundaries for now, minute rounding, and fallback time', () => {
    expect(formatTimeUntil(new Date(fixedNow.getTime()))).toBe('now');
    expect(formatTimeUntil(new Date(fixedNow.getTime() + 1_000))).toBe('in less than a minute');
    expect(formatTimeUntil(new Date(fixedNow.getTime() + 60_000))).toBe('in 1 minute');
    expect(formatTimeUntil(new Date(fixedNow.getTime() + 3_540_000))).toBe('in 59 minutes');
    expect(formatTimeUntil(new Date(fixedNow.getTime() + 3_600_000))).toBe('at 12:34:56 PM');
  });

  test.prop([fc.integer({ min: 0, max: 59 })])(
    'formatTimeAgo returns just now for dates within the last minute',
    (secondsAgo) => {
      const date = new Date(fixedNow.getTime() - secondsAgo * 1000);
      expect(formatTimeAgo(date)).toBe('just now');
    }
  );

  test.prop([fc.integer({ min: 60, max: 3599 })])(
    'formatTimeAgo returns minute granularity for dates within the last hour',
    (secondsAgo) => {
      const date = new Date(fixedNow.getTime() - secondsAgo * 1000);
      const result = formatTimeAgo(date);

      expect(result).toMatch(/^\d+m ago$/);
      expect(Number.parseInt(result, 10)).toBe(Math.floor(secondsAgo / 60));
    }
  );

  test.prop([fc.integer({ min: 0, max: 10_000 })])(
    'formatTimeUntil returns now for present or past dates',
    (secondsOffset) => {
      const date = new Date(fixedNow.getTime() - secondsOffset * 1000);
      expect(formatTimeUntil(date)).toBe('now');
    }
  );

  test.prop([fc.integer({ min: 1, max: 59 })])(
    'formatTimeUntil returns in less than a minute for near-future dates',
    (secondsAhead) => {
      const date = new Date(fixedNow.getTime() + secondsAhead * 1000);
      expect(formatTimeUntil(date)).toBe('in less than a minute');
    }
  );

  test.prop([fc.integer({ min: 60, max: 3539 })])(
    'formatTimeUntil rounds future times up to whole minutes within the hour',
    (secondsAhead) => {
      const date = new Date(fixedNow.getTime() + secondsAhead * 1000);
      const result = formatTimeUntil(date);
      const expectedMinutes = Math.ceil(secondsAhead / 60);

      expect(result).toBe(
        `in ${expectedMinutes} minute${expectedMinutes === 1 ? '' : 's'}`
      );
    }
  );
});