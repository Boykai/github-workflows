/**
 * E2E responsive regression tests for page layouts.
 *
 * Validates all application pages render without overflow, content clipping,
 * or layout breakage across all standard breakpoints.
 */

import { test, expect } from '@playwright/test';
import { VIEWPORTS } from './viewports';

/** All routes the unauthenticated app can reach (login page). */
const UNAUTHENTICATED_ROUTES = ['/login', '/'];

test.describe('Responsive Page Layouts', () => {
  for (const route of UNAUTHENTICATED_ROUTES) {
    test.describe(`Route: ${route}`, () => {
      for (const [name, viewport] of Object.entries(VIEWPORTS)) {
        test(`no horizontal overflow at ${name} (${viewport.width}x${viewport.height})`, async ({ page }) => {
          await page.setViewportSize(viewport);
          await page.goto(route);
          await expect(page.locator('body')).toBeVisible();

          const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
          const windowWidth = await page.evaluate(() => window.innerWidth);
          expect(bodyWidth).toBeLessThanOrEqual(windowWidth + 1);
        });

        test(`visible content renders at ${name} (${viewport.width}x${viewport.height})`, async ({ page }) => {
          await page.setViewportSize(viewport);
          await page.goto(route);
          // Root container should be visible
          await expect(page.locator('#root')).toBeVisible();
        });
      }
    });
  }

  test.describe('viewport transitions', () => {
    test('resizing from mobile to desktop does not break layout', async ({ page }) => {
      // Start at mobile
      await page.setViewportSize(VIEWPORTS.mobile);
      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      let overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(overflows).toBe(false);

      // Transition to tablet
      await page.setViewportSize(VIEWPORTS.tablet);
      await page.waitForTimeout(300); // Allow CSS transitions
      overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(overflows).toBe(false);

      // Transition to desktop
      await page.setViewportSize(VIEWPORTS.desktop);
      await page.waitForTimeout(300);
      overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(overflows).toBe(false);
    });

    test('resizing from desktop to mobile does not break layout', async ({ page }) => {
      // Start at desktop
      await page.setViewportSize(VIEWPORTS.desktopLarge);
      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      let overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(overflows).toBe(false);

      // Transition to tablet
      await page.setViewportSize(VIEWPORTS.tablet);
      await page.waitForTimeout(300);
      overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(overflows).toBe(false);

      // Transition to mobile
      await page.setViewportSize(VIEWPORTS.mobileSmall);
      await page.waitForTimeout(300);
      overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(overflows).toBe(false);
    });
  });
});
