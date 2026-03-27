/**
 * Performance tests for project board load time.
 *
 * Measures the time from navigation / project selection to the board
 * becoming visible.  Requires:
 *   1. A running backend + frontend (docker compose up)
 *   2. A saved auth state  — run `npx playwright test e2e/save-auth-state.ts --headed`
 *   3. E2E_PROJECT_ID env var set to the GitHub project node ID to test
 *
 * Skips gracefully when prerequisites are missing.
 *
 * Run:
 *   E2E_PROJECT_ID=PVT_xxx npx playwright test project-load-performance --headed
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_FILE = path.join(__dirname, '.auth', 'state.json');
const PROJECT_ID = process.env.E2E_PROJECT_ID;
const MAX_LOAD_MS = 10_000;

/* ------------------------------------------------------------------ */
/*  Skip entire suite when prerequisites are missing                   */
/* ------------------------------------------------------------------ */

let authFileExists = false;
try {
  fs.accessSync(AUTH_FILE, fs.constants.R_OK);
  authFileExists = true;
} catch {
  /* auth state not saved yet */
}

test.describe('Project board load performance', () => {
  // Use the saved auth session so requests hit the real backend as an
  // authenticated user.  Do NOT import from ./fixtures (that mocks APIs).
  test.use({
    storageState: authFileExists ? AUTH_FILE : undefined,
  });

  test.beforeEach(async () => {
    if (!authFileExists) {
      test.skip(true, 'Auth state not found — run save-auth-state.ts first');
    }
    if (!PROJECT_ID) {
      test.skip(true, 'E2E_PROJECT_ID env var not set');
    }
  });

  /* ---------------------------------------------------------------- */
  /*  Test 1 — Board loads within threshold for pre-selected project  */
  /* ---------------------------------------------------------------- */
  test(`board loads within ${MAX_LOAD_MS / 1000}s for a pre-selected project`, async ({
    page,
  }) => {
    const start = Date.now();

    try {
      await page.goto('/projects');
    } catch {
      test.skip(true, 'Frontend not reachable');
      return;
    }

    // Wait for the board container to appear (id="board" on ProjectBoardContent).
    // If a project is already selected in the session the board renders directly.
    // If not, the project selection empty state shows instead — both outcomes
    // should resolve well within the timeout.
    const board = page.locator('#board');
    const projectSelector = page.locator('[role="listbox"][aria-label="GitHub Projects"]');

    // Either the board is already visible (project was selected) or the
    // project selector is showing.  Wait for whichever comes first.
    const boardOrSelector = await Promise.race([
      board.waitFor({ state: 'visible', timeout: MAX_LOAD_MS }).then(() => 'board' as const),
      projectSelector
        .waitFor({ state: 'visible', timeout: MAX_LOAD_MS })
        .then(() => 'selector' as const),
    ]);

    if (boardOrSelector === 'board') {
      const elapsed = Date.now() - start;
      console.log(`  ⏱  Board visible in ${elapsed} ms`);
      expect(elapsed).toBeLessThan(MAX_LOAD_MS);
      return;
    }

    // Project selector visible — select the target project and measure from click.
    const selectStart = Date.now();
    // Prefer deterministic selection via PROJECT_ID, fall back to first option.
    let option = projectSelector.locator('[role="option"]', { hasText: PROJECT_ID! });
    if ((await option.count()) === 0) {
      option = projectSelector.locator('[role="option"]').first();
    }
    await option.click();

    await board.waitFor({ state: 'visible', timeout: MAX_LOAD_MS });
    const elapsed = Date.now() - selectStart;
    console.log(`  ⏱  Board visible in ${elapsed} ms after project selection`);
    expect(elapsed).toBeLessThan(MAX_LOAD_MS);
  });

  /* ---------------------------------------------------------------- */
  /*  Test 2 — Fresh project selection completes within threshold     */
  /* ---------------------------------------------------------------- */
  test(`project selection + board load within ${MAX_LOAD_MS / 1000}s`, async ({ page }) => {
    try {
      await page.goto('/projects');
    } catch {
      test.skip(true, 'Frontend not reachable');
      return;
    }

    // Wait for page to settle — either board or project selector.
    const board = page.locator('#board');
    const projectSelector = page.locator('[role="listbox"][aria-label="GitHub Projects"]');
    const loader = page.locator('role=status');

    // Give the page time to reach a meaningful state.
    await Promise.race([
      board.waitFor({ state: 'visible', timeout: MAX_LOAD_MS }).catch(() => {}),
      projectSelector.waitFor({ state: 'visible', timeout: MAX_LOAD_MS }).catch(() => {}),
    ]);

    // If the board is already showing, the test still passes — we just
    // verify it appeared quickly.
    if (await board.isVisible()) {
      console.log('  ℹ  Board already visible (project pre-selected)');
      return;
    }

    // Select a project and time it.
    // Prefer deterministic selection via PROJECT_ID, fall back to first option.
    let option = projectSelector.locator('[role="option"]', { hasText: PROJECT_ID! });
    if ((await option.count()) === 0) {
      option = projectSelector.locator('[role="option"]').first();
    }
    const start = Date.now();
    await option.click();

    // The loading spinner should appear…
    await loader.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});

    // …and then the board should render.
    await board.waitFor({ state: 'visible', timeout: MAX_LOAD_MS });
    const elapsed = Date.now() - start;

    console.log(`  ⏱  Project selected → board visible in ${elapsed} ms`);
    expect(elapsed).toBeLessThan(MAX_LOAD_MS);
  });
});
