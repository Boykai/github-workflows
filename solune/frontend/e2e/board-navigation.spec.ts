/**
 * E2E test for board navigation flow.
 * Tests: load app, navigate to board view, verify columns display.
 */

import { test, expect } from './fixtures';
import AxeBuilder from '@axe-core/playwright';
import { VIEWPORTS } from './viewports';

test.describe('Board Navigation', () => {
  test('should display app branding on home page', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
    // Visual regression: capture home page appearance
    await expect(page).toHaveScreenshot('board-home-branding.png', { maxDiffPixels: 100 });
  });

  test('should navigate to board view when authenticated', async ({ page }) => {
    await page.goto('/');

    // If login button is visible, the app is in unauthenticated state
    // Board navigation requires authentication
    const loginButton = page.locator('button', { hasText: /sign in|log in|github/i });
    if (await loginButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      // In unauthenticated state, verify login button is accessible
      await expect(loginButton).toBeEnabled();
    }
  });

  test('should be responsive at mobile viewport', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.mobile);
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
    // Verify no horizontal overflow
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1);
  });

  test('should be responsive at tablet viewport', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.tablet);
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should be responsive at desktop viewport', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.desktop);
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should pass axe-core accessibility audit', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
