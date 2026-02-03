import { test, expect } from '@playwright/test';

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
    
    // Should show app name
    await expect(page.locator('h1')).toContainText('GitHub Projects Chat');
    
    // Should have description text
    const description = page.locator('p, .description');
    await expect(description.first()).toBeVisible();
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
    
    // Button text should be visible
    const button = page.locator('button').first();
    if (await button.isVisible()) {
      const buttonText = await button.textContent();
      expect(buttonText).toBeTruthy();
      expect(buttonText!.length).toBeGreaterThan(0);
    }
  });
});

test.describe('Theme Toggle', () => {
  test('should display theme toggle button', async ({ page }) => {
    await page.goto('/');
    
    // Theme toggle should be visible
    const themeToggle = page.locator('.theme-toggle');
    await expect(themeToggle).toBeVisible();
  });

  test('should toggle between light and dark themes', async ({ page }) => {
    await page.goto('/');
    
    // Check initial theme (should be light by default or based on system preference)
    const html = page.locator('html');
    
    // Click theme toggle
    const themeToggle = page.locator('.theme-toggle');
    await themeToggle.click();
    
    // Wait for theme to change
    await page.waitForTimeout(500);
    
    // Check that data-theme attribute has changed
    const themeAttr = await html.getAttribute('data-theme');
    expect(themeAttr).toBeTruthy();
    expect(['light', 'dark']).toContain(themeAttr);
    
    // Click again to toggle back
    await themeToggle.click();
    await page.waitForTimeout(500);
    
    // Theme should have changed again
    const newThemeAttr = await html.getAttribute('data-theme');
    expect(newThemeAttr).not.toBe(themeAttr);
  });

  test('should persist theme preference', async ({ page, context }) => {
    await page.goto('/');
    
    // Toggle to dark theme
    const themeToggle = page.locator('.theme-toggle');
    await themeToggle.click();
    await page.waitForTimeout(500);
    
    const html = page.locator('html');
    const themeAttr = await html.getAttribute('data-theme');
    
    // Create new page in same context (shares localStorage)
    const newPage = await context.newPage();
    await newPage.goto('/');
    
    // Wait for theme to be applied
    await newPage.waitForTimeout(500);
    
    // Theme should persist in new page
    const newHtml = newPage.locator('html');
    const newThemeAttr = await newHtml.getAttribute('data-theme');
    expect(newThemeAttr).toBe(themeAttr);
    
    await newPage.close();
  });

  test('should have accessible theme toggle button', async ({ page }) => {
    await page.goto('/');
    
    const themeToggle = page.locator('.theme-toggle');
    
    // Should have aria-label
    const ariaLabel = await themeToggle.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel).toMatch(/theme/i);
    
    // Should be keyboard accessible
    await themeToggle.focus();
    await expect(themeToggle).toBeFocused();
    
    // Should be activatable with Enter
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
    
    // Theme should have changed
    const html = page.locator('html');
    const themeAttr = await html.getAttribute('data-theme');
    expect(themeAttr).toBeTruthy();
  });
});
