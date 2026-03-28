import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E test configuration.
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  /* Exclude the manual auth-save helper from default test discovery */
  testIgnore: ['**/save-auth-state.ts'],
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'e2e-report' }],
    ['list'],
  ],
  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      // Ignore visual regression snapshots for Firefox — Chromium is the baseline
      ignoreSnapshots: true,
    },
    /* Auth setup — only active when AUTH_SETUP=1, saves browser state for perf tests */
    {
      name: 'auth-setup',
      testMatch: /save-auth-state\.ts/,
      testIgnore: [],
      use: { ...devices['Desktop Chrome'] },
    },
    /* Performance tests depend on auth-setup to provide storageState */
    {
      name: 'perf',
      testMatch: /project-load-performance\.spec\.ts/,
      dependencies: ['auth-setup'],
      use: { ...devices['Desktop Chrome'] },
    },
  ].filter((p) =>
    // Include auth-setup and perf projects only when AUTH_SETUP=1
    !['auth-setup', 'perf'].includes(p.name) || process.env.AUTH_SETUP === '1',
  ),

  /* Run your local dev server before starting the tests */
  webServer: process.env.E2E_BASE_URL ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
