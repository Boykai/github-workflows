/**
 * Save authenticated browser state for performance tests.
 *
 * Opens a headed Chromium browser so you can complete GitHub OAuth login
 * manually, then saves cookies / localStorage to e2e/.auth/state.json.
 *
 * Usage:
 *   npx playwright test e2e/save-auth-state.ts --headed --project=chromium
 *
 * After running, the auth state file is reused by project-load-performance.spec.ts.
 * The .auth/ directory is git-ignored (contains tokens).
 */

import { test } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.resolve(__dirname, '.auth');
const AUTH_FILE = path.resolve(AUTH_DIR, 'state.json');
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';

test('save GitHub OAuth auth state for perf tests', async ({ browser }) => {
  if (!fs.existsSync(AUTH_DIR)) {
    fs.mkdirSync(AUTH_DIR);
  }

  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto(BASE_URL);

  // Wait for the user to complete GitHub OAuth login.
  // The page should eventually navigate away from the login screen
  // and show an authenticated view (e.g. project selector or board).
  console.log('\n🔐  Complete the GitHub OAuth login in the browser window.');
  console.log('    The script will save your session once you reach the app.\n');

  // Wait up to 120 seconds for the authenticated page to appear.
  // The auth/me endpoint returning 200 means the session is valid.
  await page.waitForResponse(
    (resp) => resp.url().includes('/api/v1/auth/me') && resp.status() === 200,
    { timeout: 120_000 },
  );

  // Small delay to let any post-login redirects and state settle.
  await page.waitForTimeout(2000);

  await context.storageState({ path: AUTH_FILE });
  console.log(`✅  Auth state saved to ${AUTH_FILE}`);

  await context.close();
});
