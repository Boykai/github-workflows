/**
 * RateLimitContext — global rate limit state shared between page hooks and the TopBar.
 *
 * Pages that consume GitHub API rate limit data (e.g. ProjectsPage) write their
 * latest computed state here via `updateRateLimit`. The TopBar reads it to display
 * the health bar at all times, regardless of which page the user is on.
 */

import { createContext, useCallback, useContext, useState } from 'react';
import type { RateLimitInfo } from '@/types';

export interface RateLimitState {
  /** Most recent rate limit snapshot, or null if not yet known. */
  info: RateLimitInfo | null;
  /** Whether any GitHub API rate-limit error is currently active. */
  hasError: boolean;
}

interface RateLimitContextValue {
  rateLimitState: RateLimitState;
  updateRateLimit: (state: RateLimitState) => void;
}

const RateLimitContext = createContext<RateLimitContextValue | undefined>(undefined);

export function RateLimitProvider({ children }: { children: React.ReactNode }) {
  const [rateLimitState, setRateLimitState] = useState<RateLimitState>({
    info: null,
    hasError: false,
  });

  const updateRateLimit = useCallback((state: RateLimitState) => {
    setRateLimitState(state);
  }, []);

  return (
    <RateLimitContext.Provider value={{ rateLimitState, updateRateLimit }}>
      {children}
    </RateLimitContext.Provider>
  );
}

export function useRateLimitStatus() {
  const ctx = useContext(RateLimitContext);
  if (ctx === undefined) {
    throw new Error('useRateLimitStatus must be used within a RateLimitProvider');
  }
  return ctx;
}
