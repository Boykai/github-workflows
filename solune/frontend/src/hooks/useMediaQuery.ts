/**
 * useMediaQuery — shared hook that wraps `window.matchMedia` for responsive behaviors.
 * Returns `true` when the provided media query string matches.
 * SSR-safe: returns `false` when `window` is not available.
 */

import { useState, useEffect } from 'react';

function getMatches(query: string): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia(query).matches;
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => getMatches(query));

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mql = window.matchMedia(query);

    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);

    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', handler);
      return () => mql.removeEventListener('change', handler);
    }

    // Fallback for older matchMedia implementations (e.g. older Safari / JSDOM)
    mql.addListener(handler);
    return () => mql.removeListener(handler);
  }, [query]);

  return matches;
}
