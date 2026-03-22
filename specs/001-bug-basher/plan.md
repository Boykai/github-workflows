# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `001-bug-basher` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash code review of the entire Solune codebase (Python backend + TypeScript/React frontend). The review audits every file against five bug categories in priority order: security vulnerabilities, runtime errors, logic bugs, test gaps, and code quality issues. Confirmed bugs are fixed directly with regression tests; ambiguous issues are documented with `TODO(bug-bash)` comments. The approach is file-by-file, category-by-category, with validation via `pytest` (backend) and `vitest` (frontend) after each batch of fixes.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, httpx, Pydantic (backend); React 19, Vite, TanStack Query, Zod, Radix UI (frontend)
**Storage**: SQLite via aiosqlite (async), file path configurable via `DATABASE_PATH` env var
**Testing**: pytest + pytest-asyncio + hypothesis (backend); vitest + @testing-library/react + Playwright (frontend)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend under `solune/`)
**Performance Goals**: N/A — this is a code quality audit, not a feature with runtime performance targets
**Constraints**: No new dependencies (FR-008); no architecture/API surface changes (FR-002); minimal focused fixes only (FR-010); preserve existing code style (FR-009)
**Scale/Scope**: ~152 Python files in backend/src, ~406 TypeScript/TSX files in frontend/src, ~190 backend test files, ~151 frontend test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1–P5 + P3 ambiguous), each with Given-When-Then acceptance scenarios |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Work is decomposed via speckit agents (specify → plan → tasks → implement) with clear handoffs |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are explicitly required by the spec (FR-003: regression test per bug fix, FR-005: full suite must pass) |
| **V. Simplicity and DRY** | ✅ PASS | Each fix is minimal and focused (FR-010), no drive-by refactors, no new abstractions |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-bug-basher/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── review-process.md
├── checklists/          # Quality checklist (from /speckit.checklist)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/              # 22 API route modules
│   │   ├── middleware/        # 5 middleware modules (admin_guard, csp, csrf, rate_limit, request_id)
│   │   ├── migrations/       # 13 SQL migration files
│   │   ├── models/           # 26 Pydantic model files
│   │   ├── prompts/          # 3 AI prompt templates
│   │   ├── services/         # 40+ service files in 8 subdirectories
│   │   │   ├── agents/
│   │   │   ├── chores/
│   │   │   ├── copilot_polling/
│   │   │   ├── github_projects/
│   │   │   ├── pipelines/
│   │   │   ├── tools/
│   │   │   └── workflow_orchestrator/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── logging_utils.py
│   │   ├── main.py
│   │   ├── protocols.py
│   │   └── utils.py
│   └── tests/
│       ├── unit/             # ~170+ unit test files
│       ├── property/         # Property-based tests (Hypothesis)
│       ├── fuzz/             # Fuzz testing
│       ├── chaos/            # Chaos testing
│       ├── concurrency/      # Concurrency tests
│       ├── integration/      # Integration tests
│       ├── architecture/     # Architecture validation
│       └── helpers/          # Test utilities
├── frontend/
│   ├── src/
│   │   ├── components/       # 43+ subdirectories, 398+ component files
│   │   ├── hooks/            # 70+ custom hooks
│   │   ├── pages/            # 17 page components
│   │   ├── services/         # API client + Zod schemas
│   │   ├── lib/              # Utility libraries
│   │   ├── utils/            # Helper utilities
│   │   ├── layout/           # Layout components
│   │   ├── constants/        # Configuration constants
│   │   ├── context/          # React contexts
│   │   ├── types/            # TypeScript type definitions
│   │   ├── test/             # Test utilities and factories
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── e2e/                  # 9 Playwright E2E spec files
└── scripts/                  # Build/validation scripts
```

**Structure Decision**: Web application (Option 2) — the existing `solune/backend/` + `solune/frontend/` structure is the target for review. No structural changes are made by this feature; the bug bash operates across both projects in-place.

## Execution Strategy

### Phase Ordering (by Bug Category Priority)

The review is executed in priority order per FR-001:

| Phase | Category | Priority | Scope | Validation |
|-------|----------|----------|-------|------------|
| 1 | Security vulnerabilities | P1 | Auth, input validation, secrets, config | `pytest` + `ruff check` + `bandit` |
| 2 | Runtime errors | P2 | Exception handling, resource leaks, null refs | `pytest` + `pyright` |
| 3 | Logic bugs | P3 | State machines, API calls, control flow, return values | `pytest` + `vitest` |
| 4 | Test gaps & quality | P4 | Mock leaks, dead assertions, missing coverage | `pytest --cov` + `vitest --coverage` |
| 5 | Code quality issues | P5 | Dead code, duplication, hardcoded values, silent failures | `ruff check` + `eslint` |

### Per-Phase Workflow

For each phase:

1. **Scan** — Audit all files in scope for the current bug category
2. **Classify** — For each finding: is it an obvious bug (fix) or ambiguous (flag)?
3. **Fix** — Apply minimal, focused fix to source code
4. **Test** — Add regression test(s) per fix
5. **Validate** — Run full test suite (`pytest` / `vitest`) + linters (`ruff` / `eslint`)
6. **Commit** — One commit per logical fix with descriptive message
7. **Report** — Add finding to summary table

### File Traversal Order

Within each phase, files are reviewed in dependency order:

1. **Backend**: `config.py` → `models/` → `services/` → `api/` → `middleware/` → `main.py`
2. **Frontend**: `types/` → `services/` → `lib/` → `utils/` → `hooks/` → `components/` → `pages/` → `layout/`
3. **Tests**: Reviewed alongside their source files (test quality is assessed in Phase 4)

### Ambiguous Issue Handling

When a finding is ambiguous (per User Story 6):
- Add `# TODO(bug-bash): <description>` comment at the code location
- Include options and rationale for deferral in the comment
- Mark as ⚠️ Flagged in summary table
- Do NOT make the code change

## Constitution Check — Post-Design Re-evaluation

*Re-check after Phase 1 design artifacts are complete.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | spec.md complete with 6 user stories, acceptance scenarios, requirements, and success criteria |
| **II. Template-Driven Workflow** | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md, and contracts/ all follow canonical templates |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan defines clear phase-based execution for the implement agent; handoff via tasks.md |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are mandatory per spec (FR-003, FR-005); regression tests required for each fix |
| **V. Simplicity and DRY** | ✅ PASS | No new abstractions introduced; each fix is minimal and focused; no complexity violations |

**Post-Design Gate Result**: ✅ ALL PASS — Ready for Phase 2 (task generation via `/speckit.tasks`).

## Complexity Tracking

> No constitution violations identified. All constraints are compatible with the bug bash approach.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
