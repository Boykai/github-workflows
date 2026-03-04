---
name: Code Clean Up
about: Recurring chore — Code Clean Up
title: '[CHORE] Code Clean Up'
labels: chore
assignees: ''
---

Codebase Cleanup: Reduce Technical Debt and Improve Maintainability

Perform a thorough codebase cleanup across the entire repository (backend, frontend, scripts, specs) to improve maintainability and reduce technical debt. Make the actual code changes.

Tech Stack Reference
See ./github/custom-instructions.md

Cleanup Categories (all equally weighted)
1. Remove Backwards-Compatibility Shims
Find and remove any compatibility layers, polyfills, or adapter code that exists only to support older API shapes, deprecated config formats, or migration-period aliases that are no longer needed.
Look for conditional branches like if old_format: / if legacy: patterns and remove the dead branch.
2. Eliminate Dead Code Paths
Remove unreachable code: functions/methods/components that are defined but never imported or called anywhere.
Remove commented-out code blocks (not documentation comments — actual commented-out logic).
Remove unused imports, unused variables, unused type definitions, and unused Pydantic models.
Remove unused route handlers (api) that have no corresponding frontend calls or test coverage.
Remove unused React components, hooks, or utility functions in the frontend.
3. Consolidate Duplicated Logic
Identify near-duplicate functions, utility helpers, or service methods that do the same thing with minor variations and consolidate them into a single implementation.
Look for copy-pasted patterns in test files (especially tests and src) that could use shared helpers or factories (existing helpers are in factories.py and mocks.py).
Consolidate duplicated API client logic in services.
Consolidate duplicated Pydantic model definitions or overlapping TypeScript types.
4. Delete Stale / Irrelevant Tests
Remove test files or test cases that test deleted or refactored functionality and are no longer meaningful.
Remove tests that mock internals so heavily they don't test real behavior.
Remove tests for code paths that no longer exist.
Clean up any test artifacts (e.g., leftover MagicMock database files visible in the workspace root of backend).
5. General Hygiene
Remove any orphaned migration files or configs that reference deleted features.
Clean up stale TODO/FIXME/HACK comments that reference completed work.
Remove unused dependencies from pyproject.toml and package.json.
Remove unused Docker Compose services or environment variables if applicable.
Constraints
All existing CI checks must pass after changes: ruff, pyright, pytest (backend); eslint, tsc, vitest, vite build (frontend).
Do not change any public API contracts (route paths, request/response shapes) — only internal implementation.
Do not remove code that is imported/called dynamically (e.g., via string-based plugin loading or migration discovery) without confirming it's truly unused.
Preserve all meaningful test coverage — only remove tests that are genuinely stale or test deleted code.
Follow existing code style: ruff defaults (double quotes, 100 char lines) for Python; strict TypeScript with @/ path alias for frontend.
Use conventional commits: refactor: for code consolidation, chore: for dead code/test removal.
Deliverables
Push all changes to a feature branch and open (or update) a PR.
In the PR description, provide a categorized summary of every change made, organized by the 5 categories above.
For each removal, briefly explain why the code was identified as dead/stale/duplicated.
Comment the results in the PR for review.
