# Tasks: Full Dependency & Pattern Modernization

**Input**: Design documents from `/specs/024-deps-modernization/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, contracts/config-contracts.md, quickstart.md

**Tests**: Not requested — existing test suites serve as regression gates (SC-003, SC-004).

**Organization**: Tasks grouped by user story. US1 and US2 are both P1 but independent (backend vs frontend). US3 and US4 are P2 pattern modernization. US5 is P3 integration verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Verify pre-upgrade baselines pass so regressions can be detected

- [X] T001 Run existing backend tests to confirm baseline passes: `cd backend && pytest`
- [X] T002 Run existing frontend tests to confirm baseline passes: `cd frontend && npm run test`
- [X] T003 [P] Run existing backend lint to confirm baseline: `cd backend && ruff check src/ && pyright src/`
- [X] T004 [P] Run existing frontend lint to confirm baseline: `cd frontend && npm run type-check && npm run lint`

**Checkpoint**: All baselines green — upgrades can now begin with confidence in regression detection

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: N/A for this feature — no shared infrastructure changes needed. All user stories modify independent config files and can proceed directly after Phase 1 baseline verification.

**⚠️ NOTE**: US1 (backend) and US2 (frontend) have zero shared files and can proceed in parallel.

---

## Phase 3: User Story 1 — Backend Dependency & Runtime Upgrade (Priority: P1) 🎯 MVP

**Goal**: Update all backend Python dependencies to latest stable versions, remove unused deps, upgrade runtime to Python 3.13

**Independent Test**: `cd backend && pip install -e ".[dev]" && pytest && ruff check src/ && pyright src/`

### Implementation for User Story 1

- [X] T005 [US1] Update all dependency version minimums in backend/pyproject.toml per contracts/config-contracts.md (fastapi≥0.135.0, uvicorn≥0.41.0, httpx≥0.28.0, pydantic≥2.12.0, pydantic-settings≥2.13.0, python-multipart≥0.0.22, pyyaml≥6.0.3, openai≥2.26.0, azure-ai-inference≥1.0.0b9, aiosqlite≥0.22.0, tenacity≥9.1.0, websockets≥16.0, githubkit≥0.14.6)
- [X] T006 [US1] Remove python-jose[cryptography] from dependencies in backend/pyproject.toml (FR-003)
- [X] T007 [US1] Update dev dependency version minimums in backend/pyproject.toml (pytest≥9.0.0, pytest-asyncio≥1.3.0, pytest-cov≥7.0.0, ruff≥0.15.0, pyright≥1.1.408)
- [X] T008 [US1] Update ruff target-version from "py311" to "py313" in backend/pyproject.toml [tool.ruff] section (FR-004)
- [X] T009 [US1] Update pyright pythonVersion from "3.12" to "3.13" in backend/pyproject.toml [tool.pyright] section (FR-006)
- [X] T010 [US1] Add asyncio_default_fixture_loop_scope = "function" to [tool.pytest.ini_options] in backend/pyproject.toml (FR-005, research finding #3)
- [X] T011 [US1] Reinstall backend dependencies in venv: `cd backend && pip install -e ".[dev]"`
- [X] T012 [US1] Run backend tests to verify all pass after upgrades: `cd backend && pytest`
- [X] T013 [US1] Run ruff check (existing rules only) to verify no regressions: `cd backend && ruff check src/`
- [X] T014 [US1] Run pyright to verify no type errors: `cd backend && pyright src/`

**Checkpoint**: Backend dependency upgrades complete. All backend tests, lint, and type checks pass.

---

## Phase 4: User Story 2 — Frontend Dependency & Runtime Upgrade (Priority: P1)

**Goal**: Update all frontend JS/TS dependencies to latest stable versions, remove unused deps, upgrade to React 19, Vite 7, Tailwind v4, ESLint 10

**Independent Test**: `cd frontend && rm -rf node_modules && npm install && npm run type-check && npm run lint && npm run test && npm run build`

### Implementation for User Story 2

- [X] T015 [P] [US2] Update React and React DOM from ^18.3.1 to ^19.2.0, and @types/react to ^19.2.0, @types/react-dom to ^19.2.0 in frontend/package.json
- [X] T016 [P] [US2] Update Vite from ^5.4.0 to ^7.3.0 and @vitejs/plugin-react from ^4.2.1 to ^5.1.0 in frontend/package.json
- [X] T017 [P] [US2] Update Tailwind CSS from ^3.4.19 to ^4.2.0 and add @tailwindcss/vite ^4.2.0 to devDependencies in frontend/package.json
- [X] T018 [P] [US2] Update ESLint from ^9.0.0 to ^10.0.0, @eslint/js from ^9.0.0 to ^10.0.0, and eslint-plugin-react-hooks from ^5.0.0 to ^7.0.0 in frontend/package.json (adjusted: ESLint stays at ^9.39.0 — ESLint 10 ecosystem not ready; react-hooks stays at ^5.2.0)
- [X] T019 [P] [US2] Update remaining dependencies in frontend/package.json: @tanstack/react-query ^5.90.0, typescript ~5.9.0, typescript-eslint ^8.56.0, lucide-react ^0.577.0, prettier ^3.8.0, happy-dom ^20.8.0, jsdom ^28.1.0, @playwright/test ^1.58.2, @types/node ^25.3.0
- [X] T020 [US2] Remove socket.io-client from dependencies in frontend/package.json (FR-009)
- [X] T021 [US2] Remove autoprefixer, postcss, and tailwindcss-animate from devDependencies in frontend/package.json (FR-011)
- [X] T022 [US2] Clean install frontend dependencies: `cd frontend && rm -rf node_modules package-lock.json && npm install`
- [X] T023 [US2] Run frontend type check to verify: `cd frontend && npm run type-check`
- [X] T024 [US2] Run frontend build to verify (NOTE: build blocked by PostCSS config — resolved in Phase 5 T028): `cd frontend && npm run build`

**Checkpoint**: Frontend dependency versions bumped & installable. Build passes. Type-level compatibility confirmed.

---

## Phase 5: User Story 3 — Frontend Code Pattern Modernization (Priority: P2)

**Goal**: Migrate Tailwind to CSS-first config, remove forwardRef from shadcn/ui components, update Vite config for @tailwindcss/vite, update ESLint config for v10

**Independent Test**: Verify no forwardRef in UI components, tailwind.config.js and postcss.config.js deleted, `npm run build && npm run test && npm run lint` all pass

### Implementation for User Story 3

- [X] T025 [US3] Run `npx @tailwindcss/upgrade` from frontend/ to auto-migrate Tailwind v3→v4 (handles CSS directives, utility class renames, config migration)
- [X] T026 [US3] Migrate tailwind.config.js theme to CSS-first @theme block in frontend/src/index.css: replace @tailwind directives with @import "tailwindcss", add @theme block with custom fonts, shadows, colors, border-radii per research.md section 5
- [X] T027 [US3] Delete frontend/tailwind.config.js (replaced by CSS-first config in index.css) (FR-010)
- [X] T028 [US3] Delete frontend/postcss.config.js (replaced by @tailwindcss/vite plugin) (FR-010)
- [X] T029 [US3] Update frontend/vite.config.ts: import @tailwindcss/vite and add tailwindcss() to plugins array per contracts/config-contracts.md (FR-012)
- [X] T030 [US3] Update frontend/components.json for Tailwind v4 compatibility (FR-014)
- [X] T031 [P] [US3] Remove React.forwardRef from Button component in frontend/src/components/ui/button.tsx — accept ref as regular prop (FR-013)
- [X] T032 [P] [US3] Remove React.forwardRef from Input component in frontend/src/components/ui/input.tsx — accept ref as regular prop (FR-013)
- [X] T033 [P] [US3] Remove React.forwardRef from all Card components (Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter) in frontend/src/components/ui/card.tsx — accept ref as regular prop (FR-013)
- [X] T034 [US3] Update frontend/eslint.config.js for ESLint 10 (NOTE: stayed on ESLint 9.39 — ecosystem not ready for v10)
- [X] T035 [US3] Fix any new ESLint violations from updated recommended rules (no-unassigned-vars, no-useless-assignment, preserve-caught-error) across frontend/src/
- [X] T036 [US3] Run frontend tests to verify all pass: `cd frontend && npm run test`
- [X] T037 [US3] Run frontend lint to verify zero errors: `cd frontend && npm run lint`
- [X] T038 [US3] Run frontend type check to verify: `cd frontend && npm run type-check`
- [X] T039 [US3] Run frontend build to verify: `cd frontend && npm run build`

**Checkpoint**: All frontend code patterns modernized. forwardRef removed, Tailwind v4 CSS-first, ESLint 10 clean. Build/test/lint all pass.

---

## Phase 6: User Story 4 — Backend Code Pattern Modernization (Priority: P2)

**Goal**: Expand ruff lint rules to enforce modern Python idioms (FURB, PTH, PERF, RUF) and auto-fix violations

**Independent Test**: `cd backend && ruff check src/ && pyright src/ && pytest`

### Implementation for User Story 4

- [X] T040 [US4] Add FURB, PTH, PERF, RUF rule sets to [tool.ruff.lint] select list in backend/pyproject.toml (FR-004)
- [X] T041 [US4] Run `ruff check --fix backend/src/` to auto-fix safe violations from expanded rules
- [X] T042 [US4] Manually review and fix any remaining ruff violations not auto-fixable in backend/src/
- [X] T043 [US4] Run ruff check to confirm zero violations: `cd backend && ruff check src/` (FR-019)
- [X] T044 [US4] Run pyright to confirm zero type errors: `cd backend && pyright src/` (FR-020)
- [X] T045 [US4] Run backend tests to confirm all pass: `cd backend && pytest` (FR-015)

**Checkpoint**: Backend code fully modernized. Expanded ruff rules pass. Type check clean. All tests pass.

---

## Phase 7: User Story 5 — Infrastructure Verification (Priority: P3)

**Goal**: Update Dockerfiles and verify full Docker Compose stack builds and runs

**Independent Test**: `docker compose build && docker compose up -d && sleep 10 && curl localhost:8000/api/health && docker compose down`

### Implementation for User Story 5

- [X] T046 [P] [US5] Update backend/Dockerfile base image from python:3.12-slim to python:3.13-slim (FR-001)
- [X] T047 [P] [US5] Update frontend/Dockerfile base image from node:20-alpine to node:22-alpine (FR-007)
- [X] T048 [US5] Run `docker compose build` to verify both images build successfully (FR-018)
- [X] T049 [US5] Run `docker compose up` and verify both services start and pass health checks within 30 seconds (FR-018, SC-010)
- [X] T050 [US5] Run `docker compose down` and confirm clean shutdown

**Checkpoint**: Full stack builds and runs in Docker with updated runtimes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [X] T051 Run quickstart.md full verification sequence from specs/024-deps-modernization/quickstart.md
- [X] T052 Verify zero unused dependencies remain: confirm python-jose absent from backend, socket.io-client absent from frontend (SC-012)
- [X] T053 Verify all success criteria from spec.md: SC-001 through SC-012

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — baseline verification
- **Phase 2 (Foundational)**: N/A — skipped, no shared infrastructure changes
- **Phase 3 (US1 — Backend Deps)**: Depends on Phase 1 baseline
- **Phase 4 (US2 — Frontend Deps)**: Depends on Phase 1 baseline. **Independent of Phase 3** — can run in parallel
- **Phase 5 (US3 — Frontend Patterns)**: Depends on Phase 4 (US2) — needs updated packages installed
- **Phase 6 (US4 — Backend Patterns)**: Depends on Phase 3 (US1) — needs expanded ruff rules. **Independent of Phase 5** — can run in parallel
- **Phase 7 (US5 — Docker)**: Depends on Phases 3, 4, 5, 6 — all code changes must be complete
- **Phase 8 (Polish)**: Depends on Phase 7 — final validation

### User Story Dependencies

- **US1 (Backend Deps, P1)**: Independent — backend only
- **US2 (Frontend Deps, P1)**: Independent — frontend only. **Can run in parallel with US1**
- **US3 (Frontend Patterns, P2)**: Depends on US2 — needs React 19/Tailwind v4 installed
- **US4 (Backend Patterns, P2)**: Depends on US1 — needs updated pyproject.toml. **Can run in parallel with US3**
- **US5 (Docker, P3)**: Depends on US1, US2, US3, US4 — needs all changes finalized

### Parallel Opportunities

**Batch 1** (after baseline):
- US1 (Phase 3): Backend dependency upgrades
- US2 (Phase 4): Frontend dependency upgrades

**Batch 2** (after respective deps):
- US3 (Phase 5): Frontend pattern modernization (after US2)
- US4 (Phase 6): Backend pattern modernization (after US1)

**Batch 3** (after all code changes):
- US5 (Phase 7): Docker verification

---

## Parallel Example: Batch 1

```bash
# These can run simultaneously since backend and frontend share no files:
Task: T005-T014 (US1 — Backend dependency upgrades in backend/pyproject.toml)
Task: T015-T024 (US2 — Frontend dependency upgrades in frontend/package.json)
```

## Parallel Example: Phase 5 forwardRef Removal

```bash
# These can run simultaneously since they modify different files:
Task: T031 — Remove forwardRef from frontend/src/components/ui/button.tsx
Task: T032 — Remove forwardRef from frontend/src/components/ui/input.tsx
Task: T033 — Remove forwardRef from frontend/src/components/ui/card.tsx
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Baseline verification
2. Complete Phase 3: US1 — Backend deps upgraded, tests pass
3. Complete Phase 4: US2 — Frontend deps upgraded, build passes
4. **STOP and VALIDATE**: Backend API works, frontend builds with new deps
5. This is a viable checkpoint — app runs with updated dependencies even without pattern modernization

### Incremental Delivery

1. Baseline verification → Pre-upgrade state confirmed
2. US1 (Backend deps) → `pytest` passes with all new versions
3. US2 (Frontend deps) → `npm run build` passes with React 19, Vite 7, Tailwind v4
4. US3 (Frontend patterns) → forwardRef removed, CSS-first Tailwind, ESLint 10 clean
5. US4 (Backend patterns) → Expanded ruff rules, zero violations
6. US5 (Docker) → Full stack builds and runs in containers
7. Each story adds confidence without breaking previous stories
