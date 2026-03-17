import { test, expect } from './fixtures';
import AxeBuilder from '@axe-core/playwright';

const protectedRoutes = ['/apps', '/help', '/tools'];

test.describe('Protected Routes', () => {
  for (const route of protectedRoutes) {
    test(`redirects unauthenticated users from ${route} to login without accessibility violations`, async ({ page }) => {
      await page.goto(route);

      await expect(page).toHaveURL(/\/login$/);
      await expect(page.locator('h2')).toContainText('Solune');

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(results.violations).toEqual([]);
    });
  }
});