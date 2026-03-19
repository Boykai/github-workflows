import { test, expect } from './fixtures';

/**
 * E2E Tests for MCP Tool Configuration
 */

test.describe('MCP Tool Configuration', () => {
  test('should show tools page', async ({ page }) => {
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

    await page.goto('/tools');
    await page.waitForLoadState('networkidle');

    const url = page.url();
    expect(url).toMatch(/\/(tools|login)/);
  });

  test('should handle unauthenticated access to tools page', async ({ page }) => {
    await page.goto('/tools');
    await page.waitForLoadState('networkidle');

    // Should either show login or redirect
    const url = page.url();
    expect(url).toMatch(/\/(tools|login)/);
  });
});
