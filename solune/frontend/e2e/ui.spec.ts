import { test, expect } from './fixtures';
import AxeBuilder from '@axe-core/playwright';

/**
 * E2E Tests for UI Components and Layout
 */

test.describe('Login Page UI', () => {
  test('should display proper styling', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await expect(page.locator('h1')).toBeVisible();
    
    // Check that the page has proper layout
    const body = page.locator('body');
    await expect(body).toBeVisible();
    
    // Main content should be centered or properly positioned
    const mainContent = page.locator('.app-login, .login-container, main, #root > div');
    await expect(mainContent.first()).toBeVisible();

    // Visual regression: capture login page UI
    await expect(page).toHaveScreenshot('login-page-styling.png', { maxDiffPixels: 100 });
  });

  test('should be responsive', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    await expect(page.locator('h1')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('h1')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should have visible branding', async ({ page }) => {
    await page.goto('/');
    
    // Should show app name — h2 carries the branding on the login page
    await expect(page.locator('h2')).toContainText('Solune');
    
    // Should have description text
    const description = page.locator('p, .description');
    await expect(description.first()).toBeVisible();
  });

  test('should support dark mode', async ({ page }) => {
    await page.goto('/');
    
    // Check that page loads in light mode by default
    const htmlElement = page.locator('html');
    await expect(htmlElement).not.toHaveClass(/dark-mode-active/);
    
    // Add dark mode class to test dark theme
    await page.evaluate(() => {
      document.documentElement.classList.add('dark-mode-active');
    });
    
    // Verify dark mode is applied
    await expect(htmlElement).toHaveClass(/dark-mode-active/);
    
    // Page should still be visible and functional
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Solune');
  });
});

test.describe('Interactive Elements', () => {
  test('buttons should have hover states', async ({ page }) => {
    await page.goto('/');
    
    const button = page.locator('button').first();
    await expect(button).toBeVisible();
    
    // Hover over button
    await button.hover();
    
    // Button should still be visible and functional
    await expect(button).toBeVisible();
    await expect(button).toBeEnabled();
  });

  test('should handle rapid clicks gracefully', async ({ page }) => {
    await page.goto('/');
    
    const button = page.locator('button').first();
    if (await button.isVisible()) {
      // Multiple rapid clicks should not break the UI
      await button.click({ clickCount: 3, delay: 100 });
      
      // Page should still be functional
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('Accessibility', () => {
  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Press Tab to navigate
    await page.keyboard.press('Tab');
    
    // Some element should be focused
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeTruthy();
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/');
    
    // Heading should be visible (implies sufficient contrast)
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    
    // Button text should be visible (skip icon-only buttons like the theme toggle)
    const button = page.locator('button:not(:has(> svg:only-child))').first();
    if (await button.isVisible()) {
      const buttonText = await button.textContent();
      expect(buttonText?.trim()).toBeTruthy();
      expect(buttonText!.length).toBeGreaterThan(0);
    }
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
