# Implementation Plan: Modernize Testing to Surface Unknown Bugs

**Branch**: `046-modernize-testing` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/046-modernize-testing/spec.md`

## Summary

The current test suite (~79 backend, ~78 frontend test files) verifies known behavior but lacks mechanisms to discover unknown bugs. This plan introduces six complementary techniques — coverage enforcement, property-based testing, mutation testing, API contract validation, visual/accessibility regression, and security/dependency scanning — to systematically surface defects the existing suite misses.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI + Pydantic (backend), React 19 + Vite 7 + TanStack Query (frontend)
**Storage**: aiosqlite (backend sessions/settings)
**Testing**: pytest + pytest-asyncio + pytest-cov (backend), Vitest 4 + happy-dom + Testing Library + Playwright 1.58 (frontend)
**Target Platform**: Linux (Docker containers, GitHub Actions CI)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: N/A — this feature targets test infrastructure, not runtime performance
**Constraints**: Mutation testing must not gate PRs (nightly/weekly schedule only); CI step additions must not significantly increase PR build time for non-mutation steps
**Scale/Scope**: ~79 backend test files, ~78 frontend test files, 11 pages (4 tested), ~15 component directories (several untested)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Specification-First | PASS | `spec.md` created with prioritized user stories, Given-When-Then acceptance scenarios, and scope boundaries |
| II. Template-Driven | PASS | Using canonical `plan-template.md`; all artifacts in `specs/046-modernize-testing/` |
| III. Agent-Orchestrated | PASS | Plan produced by `/speckit.plan`; tasks will follow via `/speckit.tasks` |
| IV. Test Optionality | PASS | This feature is *explicitly about* adding test infrastructure — tests are the core deliverable, not incidental |
| V. Simplicity / DRY | PASS | Each technique is additive configuration + targeted test files; no new abstractions or application-code refactoring |
| Branch/Dir Naming | PASS | `046-modernize-testing` follows `###-short-name` pattern |
| Phase-Based Execution | PASS | Specify → Plan (this) → Tasks → Implement |

No violations. No complexity-tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/046-modernize-testing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── pyproject.toml                    # Add hypothesis, mutmut, pip-audit, bandit deps + coverage config
│   ├── src/
│   │   ├── models/                       # Property-test targets (serialization round-trips)
│   │   ├── services/                     # Mutation-test target scope
│   │   └── ...
│   └── tests/
│       ├── unit/                         # Existing unit tests
│       ├── property/                     # NEW: Hypothesis property-based tests
│       └── ...
├── frontend/
│   ├── package.json                      # Add fast-check, @stryker-mutator/*, eslint-plugin-security, @axe-core/playwright
│   ├── vitest.config.ts                  # Add coverage thresholds
│   ├── playwright.config.ts              # Add Firefox project + visual regression config
│   ├── eslint.config.js                  # Add security plugin
│   ├── stryker.config.mjs               # NEW: Stryker mutation testing config
│   ├── src/
│   │   ├── test/
│   │   │   └── a11y-helpers.ts           # Existing — expand usage to all component tests
│   │   ├── hooks/                        # Mutation-test target scope
│   │   ├── lib/                          # Mutation-test and property-test targets
│   │   └── ...
│   └── e2e/
│       └── ...                           # Add visual regression (toHaveScreenshot) + axe-core assertions
├── scripts/
│   └── export-openapi.sh                 # NEW: Export backend OpenAPI spec for contract validation
└── ...
.github/workflows/
└── ci.yml                                # Add coverage enforcement, auditing, security linting, contract validation steps
```

**Structure Decision**: Web application (Option 2). All changes land in the existing `solune/backend/` and `solune/frontend/` structure. New test files are co-located under existing `tests/` directories. CI changes extend the existing `.github/workflows/ci.yml`. No new top-level directories.

## Complexity Tracking

> No violations. No entries required.
