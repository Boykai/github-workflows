/**
 * E2E responsive regression tests for touch targets and interactive elements.
 *
 * Validates:
 * - Interactive elements meet WCAG 44x44px minimum touch target size on mobile
 * - Buttons, links, and menu items are usable at mobile viewports
 */

import { test, expect } from '@playwright/test';
import { VIEWPORTS } from './viewports';

const MINIMUM_TOUCH_SIZE = 44;

test.describe('Touch Target Sizes', () => {
  test('interactive buttons meet 44px minimum on mobile', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.mobile);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Check all visible buttons for minimum touch target
    const buttons = page.locator('button:visible');
    const count = await buttons.count();

    // If buttons exist, verify they are touch-friendly
    if (count > 0) {
      for (let i = 0; i < Math.min(count, 10); i++) {
        const box = await buttons.nth(i).boundingBox();
        if (box) {
          // Log which button is checked for debugging
          const label = await buttons.nth(i).getAttribute('aria-label') ?? `button-${i}`;
          expect.soft(
            box.width,
            `Button "${label}" should be at least ${MINIMUM_TOUCH_SIZE}px wide`,
          ).toBeGreaterThanOrEqual(MINIMUM_TOUCH_SIZE);
          expect.soft(
            box.height,
            `Button "${label}" should be at least ${MINIMUM_TOUCH_SIZE}px tall`,
          ).toBeGreaterThanOrEqual(MINIMUM_TOUCH_SIZE);
        }
      }
    }
  });

  test('touch-target class elements meet 44px minimum', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.mobile);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    const touchTargets = page.locator('.touch-target:visible');
    const count = await touchTargets.count();

    for (let i = 0; i < count; i++) {
      const box = await touchTargets.nth(i).boundingBox();
      if (box) {
        expect.soft(
          box.width,
          `touch-target element ${i} should be at least ${MINIMUM_TOUCH_SIZE}px wide`,
        ).toBeGreaterThanOrEqual(MINIMUM_TOUCH_SIZE);
        expect.soft(
          box.height,
          `touch-target element ${i} should be at least ${MINIMUM_TOUCH_SIZE}px tall`,
        ).toBeGreaterThanOrEqual(MINIMUM_TOUCH_SIZE);
      }
    }
  });
});
