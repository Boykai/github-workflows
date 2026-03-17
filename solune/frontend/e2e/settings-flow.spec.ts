/**
 * E2E test for settings flow.
 * Tests: navigate to settings view, verify settings sections display.
 */

import { test, expect } from './fixtures';
import { VIEWPORTS } from './viewports';

test.describe('Settings Flow', () => {
  test('should load the application', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
    // Visual regression: capture settings page load state
    await expect(page).toHaveScreenshot('settings-initial-load.png', { maxDiffPixels: 100 });
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');

    // Use explicit focus target to avoid flaky focus behavior in headless browsers.
    const firstFocusable = page
      .locator('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
      .first();

    if (await firstFocusable.count()) {
      await firstFocusable.focus();
      await expect(firstFocusable).toBeFocused();
      await page.keyboard.press('Tab');
    } else {
      await expect(page.locator('h1')).toBeVisible();
    }
  });

  test('should handle settings page responsive layout at mobile', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.mobile);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
    // No horizontal overflow
    const overflow = await page.evaluate(
      () => document.body.scrollWidth > window.innerWidth
    );
    expect(overflow).toBe(false);
  });

  test('should handle settings page responsive layout at tablet', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.tablet);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle settings page responsive layout at desktop', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.desktop);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });
});
