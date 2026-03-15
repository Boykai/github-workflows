# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `001-bug-basher` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-bug-basher/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Perform a comprehensive bug bash code review of the entire Solune codebase — a monorepo containing a FastAPI backend (Python 3.13), a React/TypeScript frontend (Vite + Node 22), and supporting infrastructure (Docker, CI/CD, scripts). The review audits every file for five categories of bugs in strict priority order: security vulnerabilities, runtime errors, logic bugs, test gaps, and code quality issues. Each confirmed bug is fixed with a minimal, focused change and a new regression test. Ambiguous issues are flagged with `# TODO(bug-bash):` comments. The process completes with a summary table, green test suite, and clean linting.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript ~5.9 (frontend)
**Primary Dependencies**: FastAPI ≥0.135, Pydantic ≥2.12, React 19.2, Vite 7.3, Tailwind CSS 4.2
**Storage**: SQLite via aiosqlite (async); consolidated schema at `solune/backend/src/migrations/023_consolidated_schema.sql`
**Testing**: pytest + pytest-asyncio (backend), Vitest + happy-dom (frontend unit), Playwright (frontend E2E)
**Target Platform**: Linux server (Docker: Python 3.13-slim backend, Node 22-alpine → Nginx 1.27-alpine frontend)
**Project Type**: Web application (monorepo with backend + frontend)
**Performance Goals**: N/A — this is a code quality audit, not a feature implementation
**Constraints**: No new dependencies (FR-011), no public API changes (FR-010), no architecture changes, preserve existing code style (FR-012), each fix minimal and focused (FR-013)
**Scale/Scope**: ~23 backend services, ~19 API routes, ~20 models, ~50+ unit tests, ~4 integration tests, plus full React frontend with components/pages/hooks/services

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` exists with prioritized user stories (P1–P5), Given-When-Then acceptance scenarios, and clear scope boundaries |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Single-responsibility agent (`speckit.plan`) producing well-defined outputs |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are explicitly required by the feature spec (FR-005: "at least one new regression test per bug"); this is not default optionality but spec-mandated |
| **V. Simplicity and DRY** | ✅ PASS | Each fix must be minimal and focused (FR-013). No premature abstraction. No drive-by refactors |
| **Branch & Directory Naming** | ✅ PASS | `001-bug-basher` follows `###-short-name` convention |
| **Phase-Based Execution** | ✅ PASS | Specify → Plan (current) → Tasks → Implement → Analyze |
| **Independent User Stories** | ✅ PASS | Each bug category (P1–P5) is independently testable and delivers standalone value |
| **Constitution Supremacy** | ✅ PASS | No conflicts between constitution and templates |
| **Compliance Review** | ✅ PASS | This section fulfills the compliance requirement |

**Gate Result**: ✅ ALL GATES PASS — Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-bug-basher/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── bug-report-schema.md  # Bug report entry and summary table contract
├── checklists/
│   └── requirements.md  # Pre-existing checklist from specify phase
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/            # 19 FastAPI route modules
│   │   ├── models/         # 20 Pydantic model modules
│   │   ├── services/       # 23 service modules + 6 sub-packages
│   │   ├── middleware/      # 4 middleware modules (admin_guard, csp, rate_limit, request_id)
│   │   ├── prompts/        # 2 AI prompt template modules
│   │   ├── migrations/     # SQLite schema migrations
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── config.py       # Configuration management
│   │   ├── constants.py    # Application constants
│   │   ├── dependencies.py # FastAPI dependency injection
│   │   ├── exceptions.py   # Custom exceptions
│   │   ├── logging_utils.py # Structured logging
│   │   ├── utils.py        # Utility functions
│   │   └── attachment_formatter.py # File attachment handling
│   └── tests/
│       ├── unit/           # 50+ unit test files
│       ├── integration/    # 4 integration test files
│       ├── helpers/        # Test factories and assertions
│       ├── conftest.py     # Pytest fixtures
│       └── test_api_e2e.py # End-to-end API tests
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Page-level components
│   │   ├── layout/         # Layout components
│   │   ├── context/        # React Context state management
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API client services
│   │   ├── lib/            # Utility libraries
│   │   ├── utils/          # Utility functions
│   │   ├── types/          # TypeScript type definitions
│   │   ├── constants/      # Frontend constants
│   │   ├── test/           # Test setup & utilities
│   │   ├── App.tsx         # Root component
│   │   └── main.tsx        # Entry point
│   └── e2e/                # Playwright E2E tests
├── scripts/                # Development utility scripts
├── docs/                   # Documentation
└── docker-compose.yml      # Local dev composition

docker-compose.yml          # Root-level production composition
```

**Structure Decision**: Existing monorepo with `solune/backend/` (FastAPI + Python) and `solune/frontend/` (React + TypeScript). The bug bash operates across the full tree — no new directories are created. All fixes are made in-place within existing files.

## Complexity Tracking

> No constitution violations to justify. All gates pass.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
