import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Authentication Flow
 */

test.describe('Authentication', () => {
  test('should display login page when not authenticated', async ({ page }) => {
    await page.goto('/');
    
    // Should show the login page
    await expect(page.locator('h1')).toContainText('Front');
    await expect(page.locator('text=Manage your GitHub Projects with natural language')).toBeVisible();
    
    // Should have a login button
    const loginButton = page.locator('button:has-text("Sign in with GitHub"), button:has-text("Login"), a:has-text("Sign in")');
    await expect(loginButton.first()).toBeVisible();
  });

  test('should show login page without loading spinner', async ({ page }) => {
    await page.goto('/');
    
    // The login content should appear quickly (not stuck on loading)
    await expect(page.locator('h1')).toContainText('Front', { timeout: 5000 });
    
    // Should NOT show a loading spinner for more than briefly
    const spinner = page.locator('.spinner, .loading, [data-testid="loading"]');
    // If spinner exists, it should disappear quickly
    if (await spinner.isVisible()) {
      await expect(spinner).not.toBeVisible({ timeout: 3000 });
    }
  });

  test('login button should redirect to GitHub OAuth', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('Front');
    
    // Find and click login button
    const loginButton = page.locator('button:has-text("Sign in with GitHub"), button:has-text("Login"), button:has-text("Sign in")');
    
    if (await loginButton.first().isVisible()) {
      // Set up navigation listener before clicking
      const navigationPromise = page.waitForURL(/github\.com|localhost:8000\/api\/v1\/auth\/github/, { timeout: 5000 }).catch(() => null);
      
      await loginButton.first().click();
      
      // Should redirect to GitHub OAuth or auth endpoint
      await navigationPromise;
      const url = page.url();
      expect(url.includes('github.com') || url.includes('/auth/github')).toBeTruthy();
    }
  });
});

test.describe('Page Structure', () => {
  test('should have correct page title', async ({ page }) => {
    await page.goto('/');
    
    // Check page title
    await expect(page).toHaveTitle(/Front/i);
  });

  test('should have accessible elements', async ({ page }) => {
    await page.goto('/');
    
    // Main heading should be accessible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    
    // Button should be focusable
    const button = page.locator('button').first();
    if (await button.isVisible()) {
      await button.focus();
      await expect(button).toBeFocused();
    }
  });
});

test.describe('Error Handling', () => {
  test('should handle API errors gracefully', async ({ page }) => {
    await page.goto('/');
    
    // Page should still be functional even if API returns errors
    await expect(page.locator('h1')).toBeVisible();
    
    // Should not show raw error messages to user
    await expect(page.locator('text=/Error|Exception|undefined|null/i')).not.toBeVisible();
  });

  test('should not crash on network issues', async ({ page, context }) => {
    // Block API requests to simulate network issues
    await context.route('**/api/**', route => route.abort());
    
    await page.goto('/');
    
    // Page should still render the login UI
    await expect(page.locator('h1')).toContainText('Front');
  });
});
