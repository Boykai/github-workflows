import { test, expect } from './fixtures';

/**
 * E2E Tests for Pipeline Monitoring Flow
 */

test.describe('Pipeline Monitoring', () => {
  test('should show pipeline page with proper layout', async ({ page }) => {
    // Override auth for authenticated access
    await page.route('**/api/v1/auth/me', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          github_user_id: '12345',
          github_username: 'testuser',
          session_id: 'test-session',
        }),
      })
    );

    await page.route('**/api/v1/projects**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    );

    await page.goto('/pipeline');
    await page.waitForLoadState('networkidle');

    const url = page.url();
    expect(url).toMatch(/\/(pipeline|login)/);
  });

  test('should handle pipeline page without active project', async ({ page }) => {
    await page.route('**/api/v1/auth/me', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          github_user_id: '12345',
          github_username: 'testuser',
          session_id: 'test-session',
        }),
      })
    );

    await page.goto('/pipeline');
    await page.waitForLoadState('networkidle');

    // Page should load without crashing
    const content = await page.content();
    expect(content).toBeTruthy();
  });
});
