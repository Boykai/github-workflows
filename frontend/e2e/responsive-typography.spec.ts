/**
 * E2E responsive regression tests for typography scaling.
 *
 * Validates:
 * - Text remains readable (minimum font sizes) across viewports
 * - Headings scale proportionally from mobile to desktop
 * - No text overflow or clipping occurs
 */

import { test, expect } from '@playwright/test';
import { VIEWPORTS } from './viewports';

const MINIMUM_BODY_FONT_SIZE = 16; // px — below this text is unreadable without zoom

test.describe('Responsive Typography', () => {
  for (const [name, viewport] of Object.entries(VIEWPORTS)) {
    test(`body text is at least ${MINIMUM_BODY_FONT_SIZE}px at ${name} (${viewport.width}px)`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      const bodyFontSize = await page.evaluate(() => {
        const style = window.getComputedStyle(document.body);
        return parseFloat(style.fontSize);
      });
      expect(bodyFontSize).toBeGreaterThanOrEqual(MINIMUM_BODY_FONT_SIZE);
    });

    test(`no text-overflow clipping on visible paragraphs at ${name}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      // Check that visible paragraph elements are not clipped
      const clippedCount = await page.evaluate(() => {
        const paragraphs = document.querySelectorAll('p:not([aria-hidden="true"])');
        let clipped = 0;
        for (const p of paragraphs) {
          const rect = p.getBoundingClientRect();
          // Element is outside viewport to the right → potential overflow
          if (rect.left + rect.width > window.innerWidth + 2) {
            clipped++;
          }
        }
        return clipped;
      });
      expect(clippedCount).toBe(0);
    });
  }

  test('heading font size scales from mobile to desktop', async ({ page }) => {
    // Measure heading size at mobile
    await page.setViewportSize(VIEWPORTS.mobile);
    await page.goto('/');
    const h1 = page.locator('h1').first();
    await expect(h1).toBeVisible();

    const mobileFontSize = await h1.evaluate((el) =>
      parseFloat(window.getComputedStyle(el).fontSize),
    );

    // Measure heading size at desktop
    await page.setViewportSize(VIEWPORTS.desktopLarge);
    await expect(h1).toBeVisible();

    const desktopFontSize = await h1.evaluate((el) =>
      parseFloat(window.getComputedStyle(el).fontSize),
    );

    // Desktop heading should be at least as large as mobile heading
    expect(desktopFontSize).toBeGreaterThanOrEqual(mobileFontSize);
  });
});
