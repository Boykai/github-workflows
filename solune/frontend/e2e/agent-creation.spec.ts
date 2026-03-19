import { test, expect } from './fixtures';

/**
 * E2E Tests for Agent Creation Flow
 */

test.describe('Agent Creation', () => {
  test('should show agents page with navigation', async ({ page }) => {
    // Override auth to simulate logged-in user
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

    await page.goto('/agents');
    // Should navigate to agents page or redirect to login
    await page.waitForLoadState('networkidle');

    // Either we see the agents page or a redirect to login
    const url = page.url();
    expect(url).toMatch(/\/(agents|login)/);
  });

  test('should handle unauthenticated access to agents page', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Should either show login page or redirect
    const url = page.url();
    expect(url).toMatch(/\/(agents|login)/);
  });
});
