import { lazy, type ComponentType } from 'react';

const RELOAD_KEY = 'solune-chunk-reload';

/**
 * Wraps React.lazy() with retry logic for stale dynamic imports.
 *
 * When Vite rebuilds with new chunk hashes, users with stale tabs get
 * "error loading dynamically imported module". This helper catches that
 * error and does a single page reload to fetch fresh assets. A
 * sessionStorage flag prevents infinite reload loops.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function lazyWithRetry<T extends ComponentType<any>>(
  factory: () => Promise<{ default: T }>
) {
  return lazy(async () => {
    const hasReloaded = sessionStorage.getItem(RELOAD_KEY);

    try {
      const module = await factory();
      // Import succeeded — clear the reload flag so future failures can retry
      sessionStorage.removeItem(RELOAD_KEY);
      return module;
    } catch (error) {
      if (!hasReloaded) {
        sessionStorage.setItem(RELOAD_KEY, '1');
        window.location.reload();
        // Return a never-resolving promise to prevent React from rendering
        // while the browser reloads.
        return new Promise(() => {});
      }
      // Already reloaded once — rethrow so the error boundary catches it
      throw error;
    }
  });
}
