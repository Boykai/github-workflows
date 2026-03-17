/**
 * E2E test for responsive board layout at mobile/tablet/desktop viewports.
 */

import { test, expect } from './fixtures';
import { VIEWPORTS } from './viewports';

test.describe('Responsive Board Layout', () => {
  for (const [name, viewport] of Object.entries(VIEWPORTS)) {
    test(`should render without overflow at ${name} (${viewport.width}x${viewport.height})`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      // Verify no horizontal overflow
      const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
      const windowWidth = await page.evaluate(() => window.innerWidth);
      expect(bodyScrollWidth).toBeLessThanOrEqual(windowWidth + 1);
    });

    test(`should have readable text at ${name} viewport`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');
      const h1 = page.locator('h1');
      await expect(h1).toBeVisible();
    });
  }
});
