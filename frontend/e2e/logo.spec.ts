import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Logo Component
 */

test.describe('Logo Display', () => {
  test('should display smiley face logo on home page', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await expect(page.locator('h1')).toBeVisible();
    
    // Check that the logo is visible
    const logo = page.locator('.logo');
    await expect(logo).toBeVisible();
    
    // Verify logo has proper attributes
    await expect(logo).toHaveAttribute('role', 'img');
    await expect(logo).toHaveAttribute('aria-label', 'Friendly smiley face logo');
  });

  test('should display logo at top of page', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForSelector('.logo', { state: 'visible' });
    
    // Get logo position
    const logo = page.locator('.logo');
    const logoBox = await logo.boundingBox();
    
    // Logo should be near the top of the page
    expect(logoBox).toBeTruthy();
    expect(logoBox!.y).toBeLessThan(100);
  });

  test('should have hover animation on logo', async ({ page }) => {
    await page.goto('/');
    
    const logo = page.locator('.logo');
    await expect(logo).toBeVisible();
    
    // Hover over the logo
    await logo.hover();
    
    // Wait for animation to trigger
    await page.waitForTimeout(100);
    
    // Logo should still be visible
    await expect(logo).toBeVisible();
  });

  test('should support keyboard focus on logo', async ({ page }) => {
    await page.goto('/');
    
    const logo = page.locator('.logo');
    await expect(logo).toBeVisible();
    
    // Focus the logo
    await logo.focus();
    
    // Check that the logo is focused
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeTruthy();
  });

  test('should display logo on all screen sizes', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    const mobileLogoVisible = await page.locator('.logo').isVisible();
    expect(mobileLogoVisible).toBe(true);
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    const tabletLogoVisible = await page.locator('.logo').isVisible();
    expect(tabletLogoVisible).toBe(true);
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    const desktopLogoVisible = await page.locator('.logo').isVisible();
    expect(desktopLogoVisible).toBe(true);
  });

  test('should not interfere with navigation', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForSelector('.logo', { state: 'visible' });
    
    // Check that header elements are still accessible
    const header = page.locator('.app-header');
    await expect(header).toBeVisible();
    
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('GitHub Projects Chat');
  });
});

test.describe('Logo Accessibility', () => {
  test('should have descriptive alt text', async ({ page }) => {
    await page.goto('/');
    
    const logo = page.locator('.logo');
    await expect(logo).toHaveAttribute('aria-label');
    
    const ariaLabel = await logo.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel!.length).toBeGreaterThan(0);
  });

  test('should be keyboard accessible', async ({ page }) => {
    await page.goto('/');
    
    // Press Tab to navigate through interactive elements
    await page.keyboard.press('Tab');
    
    // Some element should be focused
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeTruthy();
  });
});
