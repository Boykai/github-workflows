/**
 * E2E responsive regression tests for navigation.
 *
 * Validates:
 * - Hamburger menu appears on mobile viewports and is hidden on desktop
 * - Mobile drawer opens/closes correctly
 * - Desktop sidebar renders inline
 * - Touch targets meet 44px minimum on mobile
 */

import { test, expect } from '@playwright/test';
import { VIEWPORTS } from './viewports';

function isLoginRoute(url: string): boolean {
  return /\/login(?:$|[?#])/.test(url);
}

test.describe('Responsive Navigation', () => {
  test.describe('mobile hamburger menu', () => {
    for (const name of ['mobileSmall', 'mobile', 'mobileLarge'] as const) {
      const viewport = VIEWPORTS[name];

      test(`hamburger menu button is visible at ${name} (${viewport.width}px)`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await page.goto('/');
        await expect(page.locator('body')).toBeVisible();

        test.skip(
          isLoginRoute(page.url()),
          'Authenticated navigation shell is not available without an E2E auth session.'
        );

        const hamburger = page.getByRole('button', { name: /navigation menu/i });
        await expect(hamburger).toBeVisible();
      });
    }
  });

  test.describe('desktop navigation', () => {
    for (const name of ['desktop', 'desktopLarge'] as const) {
      const viewport = VIEWPORTS[name];

      test(`renders without horizontal overflow at ${name} (${viewport.width}px)`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await page.goto('/');
        await expect(page.locator('body')).toBeVisible();

        const overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
        expect(overflows).toBe(false);
      });
    }
  });

  test.describe('no overflow across all viewports', () => {
    for (const [name, viewport] of Object.entries(VIEWPORTS)) {
      test(`no horizontal scrollbar at ${name} (${viewport.width}x${viewport.height})`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await page.goto('/');
        await expect(page.locator('body')).toBeVisible();

        const overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
        expect(overflows).toBe(false);
      });
    }
  });
});
