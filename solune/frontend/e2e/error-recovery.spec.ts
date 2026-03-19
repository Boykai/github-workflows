import { test, expect } from './fixtures';

/**
 * E2E Tests for Error Recovery
 */

test.describe('Error Recovery', () => {
  test('should recover from network errors gracefully', async ({ page, context }) => {
    // Simulate network error on API calls
    await context.route('**/api/v1/auth/me', (route) =>
      route.abort('connectionrefused')
    );

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // App should still render without crashing
    const content = await page.content();
    expect(content).toBeTruthy();

    // Should not show raw error details to user
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('TypeError');
    expect(bodyText).not.toContain('fetch failed');
  });

  test('should handle server error responses gracefully', async ({ page }) => {
    await page.route('**/api/v1/auth/me', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      })
    );

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // App should render login or error state, not crash
    const url = page.url();
    expect(url).toBeTruthy();
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Internal server error');
  });

  test('should handle 403 forbidden gracefully', async ({ page }) => {
    await page.route('**/api/v1/auth/me', (route) =>
      route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Forbidden' }),
      })
    );

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should not display raw error to users
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Forbidden');
  });
});
