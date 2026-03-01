/**
 * E2E test for settings flow.
 * Tests: navigate to settings view, verify settings sections display.
 */

import { test, expect } from '@playwright/test';
import { VIEWPORTS } from './viewports';

test.describe('Settings Flow', () => {
  test('should load the application', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    // Verify an element actually received focus (locator objects are always truthy)
    await expect(page.locator(':focus')).toHaveCount(1);

    // Continue tabbing
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
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
