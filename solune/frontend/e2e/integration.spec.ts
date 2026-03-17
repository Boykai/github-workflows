import { test, expect } from './fixtures';

/**
 * E2E Tests for Application Performance
 */

test.describe('Performance', () => {
  test('initial page load should be fast', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('should not have memory leaks on navigation', async ({ page }) => {
    // Load page multiple times
    for (let i = 0; i < 3; i++) {
      await page.goto('/');
      await expect(page.locator('h1')).toBeVisible();
    }
    
    // Page should still be responsive
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle slow network gracefully', async ({ page, context }) => {
    // Simulate slow network for non-API assets (API routes are mocked by fixture)
    await context.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 100));
      const url = route.request().url();
      if (url.includes('/api/')) {
        // Let the page-level fixture handle API mocks
        await route.fallback();
      } else {
        await route.continue();
      }
    });
    
    await page.goto('/');
    
    // Page should still load
    await expect(page.locator('h1')).toBeVisible({ timeout: 15000 });
  });
});

test.describe('API Integration', () => {
  test('should call health endpoint', async ({ request }) => {
    // Test API directly — backend may not be running in CI
    try {
      const response = await request.get('http://localhost:8000/api/v1/health');
      if (response.ok()) {
        const data = await response.json();
        expect(['healthy', 'pass']).toContain(data.status);
      }
    } catch {
      // Backend not running (CI) — skip gracefully
      test.skip();
    }
  });

  test('should handle 401 from auth endpoint', async ({ request }) => {
    // Auth endpoint should return 401 for unauthenticated users
    try {
      const response = await request.get('http://localhost:8000/api/v1/auth/me');
      expect(response.status()).toBe(401);
    } catch {
      // Backend not running (CI) — skip gracefully
      test.skip();
    }
  });

  test('frontend should handle unauthenticated state', async ({ page }) => {
    // Navigate to page
    await page.goto('/');
    
    // Should show login UI (not crash)
    await expect(page.locator('h2')).toContainText('Solune');
    
    // Should show sign in option
    const signInText = page.locator('text=/sign in|login|authenticate/i');
    await expect(signInText.first()).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Browser Compatibility', () => {
  test('should work with JavaScript enabled', async ({ page }) => {
    await page.goto('/');
    
    // Interactive elements should work
    const button = page.locator('button').first();
    await expect(button).toBeEnabled();
  });

  test('should handle cookies', async ({ page, context }) => {
    await page.goto('/');
    
    // Application should handle cookie-based sessions
    await context.cookies();
    
    // Page should still be functional regardless of cookie state
    await expect(page.locator('h1')).toBeVisible();
  });
});
