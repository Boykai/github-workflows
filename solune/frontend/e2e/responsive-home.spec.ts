/**
 * E2E test for responsive home layout at mobile/tablet/desktop viewports.
 */

import { test, expect } from './fixtures';
import { VIEWPORTS } from './viewports';

test.describe('Responsive Home Layout', () => {
  for (const [name, viewport] of Object.entries(VIEWPORTS)) {
    test(`should render without overflow at ${name} (${viewport.width}x${viewport.height})`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      // Verify no horizontal overflow
      const overflows = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(overflows).toBe(false);
    });

    test(`should display visible heading at ${name}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await expect(page.locator('h1')).toBeVisible();
    });
  }
});
