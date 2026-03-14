# Implementation Plan: Code Quality & Technical Debt Overhaul

**Branch**: `033-code-quality-overhaul` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/033-code-quality-overhaul/spec.md`

## Summary

Systematic 6-phase refactoring across a 121K-LOC full-stack application to reduce cyclomatic complexity (8 functions scoring 42–123 → all below 25), eliminate DRY violations across 8+ files (~230 lines removed), decompose the 5,338-line God class into domain-specific services, modernize frontend components, adopt structured JSON logging backend-wide, and harden infrastructure with dependency pinning. Each phase is a self-contained commit with all tests passing.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI ≥0.135, httpx ≥0.28, Pydantic ≥2.12, github-copilot-sdk ≥0.1.30, React 19.2, TanStack Query 5.90, Vite 7.3, Tailwind 4.2
**Storage**: aiosqlite (session/settings), in-memory dict (chat messages → SQLite in Phase 3)
**Testing**: pytest + pytest-asyncio (backend, 68 test files, ~36K LOC), Vitest 4.0 + Playwright 1.58 (frontend)
**Target Platform**: Linux Docker containers (python:3.13-slim backend, node:22-alpine → nginx frontend)
**Project Type**: Web application (backend + frontend)
**Linting**: ruff + pyright basic mode (backend), ESLint 9.39 + TypeScript strict (frontend)
**Performance Goals**: Maintain current response times; no additional latency from refactoring
**Constraints**: Zero regressions — all existing tests pass after each phase. No public API changes.
**Scale/Scope**: 43K backend LOC, 42K frontend LOC, 37K test LOC, 100+ Pydantic models, 83 methods in God class

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development — **PASS**

The feature has a complete `spec.md` with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 30 functional requirements, 10 measurable success criteria, scope boundaries, and 3 resolved clarifications. No implementation began before specification.

### Principle II: Template-Driven Workflow — **PASS**

All artifacts follow canonical templates: `spec.md` used the spec template, this `plan.md` follows the plan template. No custom sections without justification.

### Principle III: Agent-Orchestrated Execution — **PASS**

Workflow followed: `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` (this). Each agent produced its defined output before handoff.

### Principle IV: Test Optionality with Clarity — **PASS (Tests Required)**

The spec explicitly mandates tests (FR-026: every refactored high-complexity function MUST have dedicated unit tests; SC-006: 70% line coverage for refactored modules). This is justified — refactoring high-complexity code without test coverage would be reckless.

### Principle V: Simplicity and DRY — **PASS**

The entire feature exists to enforce Simplicity and DRY. No new abstractions are being created for their own sake; each extraction addresses a measured duplication or complexity hotspot. The new frontend dependency (react-hook-form) is justified by eliminating significant boilerplate. The existing `StructuredJsonFormatter` in `logging_utils.py` is sufficient for structured logging — no new logging library needed (see research.md R-001). See Complexity Tracking for the only potential concern.

## Project Structure

### Documentation (this feature)

```text
specs/033-code-quality-overhaul/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions & best practices
├── data-model.md        # Phase 1: new dataclasses, enums, service interfaces
├── quickstart.md        # Phase 1: developer guide for the refactored architecture
├── contracts/           # Phase 1: service interface contracts
│   ├── github-base-client.md
│   ├── domain-services.md
│   └── structured-logging.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/              # 20 files, 100+ Pydantic models (extend with new return types)
│   ├── services/
│   │   ├── github_projects/
│   │   │   ├── service.py        # 5,338 → <1,500 lines (incrementally reduced, no facade)
│   │   │   ├── base_client.py    # NEW: shared HTTP/caching/rate-limit infrastructure
│   │   │   ├── issues.py         # NEW: GitHubIssuesService
│   │   │   ├── pull_requests.py  # NEW: GitHubPullRequestService
│   │   │   ├── branches.py       # NEW: GitHubBranchService
│   │   │   ├── projects.py       # NEW: GitHubProjectBoardService
│   │   │   ├── rate_limit.py     # NEW: RateLimitManager
│   │   │   ├── identities.py     # NEW: bot detection utilities
│   │   │   └── graphql.py        # Existing query constants (unchanged)
│   │   ├── copilot_polling/
│   │   │   ├── agent_output.py   # 1,100 → split into focused helpers (<200 each)
│   │   │   ├── recovery.py       # 800 → split into focused helpers
│   │   │   ├── pipeline.py       # 2,286 lines (complexity reduction via data-driven steps)
│   │   │   └── polling_loop.py   # 500 → data-driven step list
│   │   ├── workflow_orchestrator/
│   │   │   └── orchestrator.py   # 2,329 → extract agent resolution helpers
│   │   └── cleanup_service.py    # 1,076 → extract linking strategy functions
│   ├── api/
│   │   ├── chat.py               # 1,057 → extract command handlers + SQLite migration
│   │   ├── workflow.py           # Remove _get_repository_info() duplicate
│   │   ├── board.py              # Adopt cached_fetch() and error helpers
│   │   ├── projects.py           # Adopt cached_fetch() and error helpers
│   │   └── tasks.py              # Adopt require_selected_project()
│   ├── dependencies.py           # Update DI for new domain services
│   ├── logging_utils.py          # Already has StructuredJsonFormatter — wire it up
│   └── utils.py                  # Canonical resolve_repository() (callers consolidated here)
└── tests/
    ├── conftest.py               # Consolidate mock factories here
    ├── helpers/
    │   ├── factories.py          # Keep data factories
    │   └── mocks.py              # Merge into conftest.py, then delete
    └── unit/                     # Add tests for refactored high-complexity functions

frontend/
├── src/
│   ├── components/
│   │   ├── settings/
│   │   │   ├── GlobalSettings.tsx        # 334 → split into section components (<100 each)
│   │   │   ├── AISettingsSection.tsx      # NEW
│   │   │   ├── DisplaySettings.tsx        # NEW
│   │   │   ├── WorkflowSettings.tsx       # NEW
│   │   │   └── NotificationSettings.tsx   # NEW
│   │   └── login/
│   │       └── AnimatedBackground.tsx     # NEW: extracted from LoginPage
│   ├── hooks/
│   │   ├── usePipelineConfig.ts           # 616 → split into focused hooks (<200 each)
│   │   ├── usePipelineBoard.ts            # NEW
│   │   ├── usePipelineValidation.ts       # NEW
│   │   ├── usePipelineModelOverride.ts    # NEW
│   │   └── useAgentConfig.ts              # 354 → extract case-insensitive logic
│   ├── lib/
│   │   ├── case-utils.ts                  # NEW: case-insensitive key matching
│   │   └── time-utils.ts                  # NEW: shared time calculations
│   └── pages/
│       └── LoginPage.tsx                  # 129 → extract decorative background
└── tests/
```

**Structure Decision**: Web application structure. Backend and frontend are separate top-level directories with independent build systems and test suites. New files are added within existing directory conventions — no new top-level directories.

## Complexity Tracking

> Potential concerns from Constitution Principle V (Simplicity and DRY)

| Concern | Why Needed | Simpler Alternative Rejected Because |
|---------|------------|-------------------------------------|
| ~No new logging library needed~ | FR-027 requires structured JSON logging; `StructuredJsonFormatter` already exists in `logging_utils.py` (research.md R-001) | Wire existing formatter as root handler — no new dependency required |
| New dependency: `react-hook-form` + `zod` | FR-021 eliminates manual flatten/unflatten form state cycles (~40 lines of boilerplate per form) | Refactoring inline state with `useReducer` alone doesn't solve the unflatten problem |
| 7 new files in `github_projects/` | FR-014 God class split requires domain-specific modules | Keeping domain services in one file defeats the purpose; 7 focused files < 800 lines each is cleaner than 1 × 5,338 |
