/* eslint-disable react-hooks/rules-of-hooks */
/**
 * Shared Playwright fixtures for E2E smoke tests.
 *
 * Provides a custom `test` that automatically intercepts `/api/**` requests,
 * returning lightweight stub responses so the Vite dev-server proxy never
 * attempts to reach a backend (which isn't running in CI).
 *
 * Usage — replace `import { test, expect } from '@playwright/test'` with:
 *   import { test, expect } from './fixtures';
 */

import { test as base, expect } from '@playwright/test';

/**
 * Extend the default `test` to mock every `/api/**` request before each test.
 * Individual specs can still override routes via `page.route` / `context.route`.
 */
export const test = base.extend({
  page: async ({ page }, use) => {
    // Intercept all API calls so the Vite proxy never hits the missing backend.
    await page.route('**/api/**', (route) => {
      const url = new URL(route.request().url());

      // /api/v1/auth/me → 401 (unauthenticated)
      if (url.pathname.includes('/auth/me')) {
        return route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not authenticated' }),
        });
      }

      // /api/v1/health → 200
      if (url.pathname.includes('/health')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'healthy' }),
        });
      }

      // Everything else → 404
      return route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not found' }),
      });
    });

    await use(page);
  },
});

export { expect };
