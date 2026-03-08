import { useState, useEffect, useRef } from 'react';

/**
 * Cycles through an array of placeholder strings at a configurable interval.
 * Respects `prefers-reduced-motion` — falls back to the first prompt when
 * the user prefers reduced motion or when cycling is disabled.
 */
export function useCyclingPlaceholder(
  prompts: string[],
  options?: {
    /** Interval in milliseconds between prompt changes (default: 5000) */
    intervalMs?: number;
    /** Set to false to pause cycling (e.g. when input is focused or non-empty) */
    enabled?: boolean;
  },
): string {
  const intervalMs = options?.intervalMs ?? 5000;
  const enabled = options?.enabled ?? true;
  const [index, setIndex] = useState(0);
  const prefersReducedMotion = useRef(false);

  // Check reduced motion preference once on mount
  useEffect(() => {
    prefersReducedMotion.current =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }, []);

  useEffect(() => {
    if (!enabled || prefersReducedMotion.current || prompts.length <= 1) return;

    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % prompts.length);
    }, intervalMs);

    return () => clearInterval(timer);
  }, [prompts.length, intervalMs, enabled]);

  // Reset to 0 when disabled so the cycle restarts cleanly
  useEffect(() => {
    if (!enabled) setIndex(0);
  }, [enabled]);

  if (prefersReducedMotion.current) return prompts[0] ?? '';
  return prompts[index] ?? '';
}
