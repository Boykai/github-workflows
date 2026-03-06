# Implementation Plan: Full Dependency & Pattern Modernization

**Branch**: `024-deps-modernization` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/024-deps-modernization/spec.md`

## Summary

Upgrade all backend (Python) and frontend (JS/TS) dependencies to their latest stable versions, upgrade runtimes (Python 3.12→3.13, Node 20→22), migrate frontend toolchain (React 18→19, Tailwind v3→v4, Vite 5→7, ESLint 9→10), remove unused dependencies (python-jose, socket.io-client), expand ruff lint rules (FURB, PTH, PERF, RUF), and update code patterns to match new library APIs and modern idioms. No architectural changes, no new features — strictly dependency and pattern modernization.

## Technical Context

**Language/Version**: Python 3.12→3.13 (backend), TypeScript 5.8→5.9 (frontend), Node 20→22
**Primary Dependencies**: FastAPI, React, Vite, Tailwind CSS, TanStack Query, Pydantic
**Storage**: SQLite via aiosqlite (no schema changes)
**Testing**: pytest + pytest-asyncio (backend), Vitest + Playwright (frontend)
**Target Platform**: Docker Compose (Linux containers), nginx reverse proxy
**Project Type**: web (backend/ + frontend/)
**Performance Goals**: N/A — upgrades must not degrade existing behavior
**Constraints**: All existing tests must pass; zero lint/type errors; zero visual regressions
**Scale/Scope**: ~15 backend source files, ~30 frontend source files, 2 Dockerfiles, 3 config files to delete

### Backend Version Matrix (PyPI)

| Package | Current Min | Target | Breaking? |
|---------|------------|--------|-----------|
| fastapi | ≥0.109.0 | ≥0.135.0 | No |
| uvicorn[standard] | ≥0.27.0 | ≥0.41.0 | No |
| githubkit | ≥0.14.0 | ≥0.14.6 | No |
| httpx | ≥0.26.0 | ≥0.28.0 | No |
| pydantic | ≥2.5.0 | ≥2.12.0 | No |
| pydantic-settings | ≥2.1.0 | ≥2.13.0 | No |
| python-multipart | ≥0.0.6 | ≥0.0.22 | No |
| pyyaml | ≥6.0.1 | ≥6.0.3 | No |
| github-copilot-sdk | ≥0.1.30 | ≥0.1.30 | Same |
| openai | ≥2.24.0 | ≥2.26.0 | No |
| azure-ai-inference | ≥1.0.0b1 | ≥1.0.0b9 | No (beta) |
| aiosqlite | ≥0.20.0 | ≥0.22.0 | No |
| tenacity | ≥8.2.0 | ≥9.1.0 | No (verified: retry, stop_after_attempt, wait_exponential, before_sleep_log all preserved) |
| websockets | ≥12.0 | ≥16.0 | No (verified: connect(), ConnectionClosed preserved) |
| python-jose | ≥3.3.0 | **REMOVE** | Unused — not imported anywhere |
| pytest | ≥7.4.0 | ≥9.0.0 | Minor |
| pytest-asyncio | ≥0.23.0 | ≥1.3.0 | Yes (asyncio_mode config update needed) |
| pytest-cov | ≥4.1.0 | ≥7.0.0 | No |
| ruff | ≥0.9.0 | ≥0.15.0 | No |
| pyright | ≥1.1.400 | ≥1.1.408 | No |

### Frontend Version Matrix (npm)

| Package | Current | Target | Breaking? |
|---------|---------|--------|-----------|
| react | ^18.3.1 | ^19.2.0 | Yes (forwardRef removal, ref-as-prop) |
| react-dom | ^18.3.1 | ^19.2.0 | Yes (paired with react) |
| vite | ^5.4.0 | ^7.3.0 | Yes (config API, plugin compat) |
| @vitejs/plugin-react | ^4.2.1 | ^5.1.0 | Yes (Vite 7 compat) |
| tailwindcss | ^3.4.19 | ^4.2.0 | Yes (CSS-first @theme, @import) |
| @tailwindcss/vite | NEW | ^4.2.0 | New dependency |
| @tanstack/react-query | ^5.17.0 | ^5.90.0 | No |
| typescript | ~5.8.0 | ~5.9.0 | No |
| eslint | ^9.0.0 | ^10.0.0 | Yes (config API) |
| @eslint/js | ^9.0.0 | ^10.0.0 | Yes (paired with eslint) |
| eslint-plugin-react-hooks | ^5.0.0 | ^7.0.0 | Yes |
| typescript-eslint | ^8.0.0 | ^8.56.0 | No |
| vitest | ^4.0.18 | ^4.0.18 | Same |
| @playwright/test | ^1.58.1 | ^1.58.2 | No |
| lucide-react | ^0.575.0 | ^0.577.0 | No |
| @types/react | ^18.3.0 | ^19.2.0 | Yes (React 19 types) |
| @types/react-dom | ^18.3.0 | ^19.2.0 | Yes (React 19 types) |
| prettier | ^3.2.0 | ^3.8.0 | No |
| happy-dom | ^20.6.3 | ^20.8.0 | No |
| jsdom | ^27.4.0 | ^28.1.0 | Minor |
| postcss | ^8.5.6 | **REMOVE** | Replaced by @tailwindcss/vite |
| autoprefixer | ^10.4.27 | **REMOVE** | Built into Tailwind v4 |
| tailwindcss-animate | ^1.0.7 | **REMOVE** | Built into Tailwind v4 |
| socket.io-client | ^4.7.4 | **REMOVE** | Unused — native WebSocket API used |

**Spec Corrections**: The spec references "Vite 6" (FR-008) but the actual latest stable is Vite **7.3.1**. The spec references ESLint continuation at v9 but the actual latest is ESLint **10.0.2**. This plan targets these actual latest versions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — PASS
Feature work began with explicit specification (spec.md) containing 5 prioritized user stories (P1-P3), Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations.

### II. Template-Driven Workflow — PASS
All artifacts follow canonical templates: spec.md from spec-template, plan.md from plan-template. No custom sections added without justification.

### III. Agent-Orchestrated Execution — PASS
Workflow follows the specify → plan → tasks → implement sequence. Each phase produces specific outputs and hands off to the next agent.

### IV. Test Optionality with Clarity — PASS
The spec explicitly requires all existing tests to pass (SC-003, SC-004) but does not mandate writing new tests. This is a dependency upgrade — existing test suites serve as regression gates. No TDD phase needed.

### V. Simplicity and DRY — PASS
Changes are strictly scoped to dependency upgrades and minimum-necessary code modifications. No new abstractions, no architectural refactoring, no premature optimization. The spec's out-of-scope section is explicit about this.

**GATE RESULT: ALL PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/024-deps-modernization/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file
├── research.md          # Phase 0: version research & migration strategies
├── data-model.md        # Phase 1: N/A for this feature (no data model changes)
├── quickstart.md        # Phase 1: verification commands
├── contracts/           # Phase 1: config file contracts (pyproject.toml, package.json, etc.)
├── checklists/
│   └── requirements.md  # Quality checklist (completed)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml           # Dependency versions, ruff/pyright/pytest config
├── Dockerfile               # Python 3.12→3.13 base image
├── src/
│   ├── services/
│   │   ├── signal_delivery.py   # tenacity retry usage
│   │   └── signal_bridge.py     # websockets connect() usage
│   └── ...                      # Other src files (no breaking changes expected)
└── tests/                       # Regression gate — all must pass

frontend/
├── package.json             # Dependency versions
├── Dockerfile               # Node 20→22 base image
├── vite.config.ts           # Vite 5→7, add @tailwindcss/vite plugin
├── tailwind.config.js       # DELETE (replaced by CSS-first config)
├── postcss.config.js        # DELETE (replaced by @tailwindcss/vite)
├── eslint.config.js         # ESLint 9→10 flat config update
├── components.json          # shadcn/ui config update for Tailwind v4
├── src/
│   ├── index.css            # @tailwind directives → @import "tailwindcss" + @theme
│   └── components/ui/       # Remove React.forwardRef from button, input, card
└── tests/                   # Regression gate — all must pass

docker-compose.yml           # Verify builds with updated images
```

**Structure Decision**: Web application layout (backend/ + frontend/). No new directories created. All changes are in-place modifications to existing files, plus deletion of 3 obsolete config files.

## Complexity Tracking

> No constitution violations. No complexity justification needed.
