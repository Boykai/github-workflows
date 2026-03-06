# Implementation Plan: Bug Bash — Full Codebase Review & Fix

**Branch**: `025-bug-basher` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash of the entire codebase (90 backend Python source files, 87 frontend TypeScript/React source files, 59 backend test files, 42 frontend test files). Audit every file for five categories of bugs in priority order: security vulnerabilities, runtime errors, logic bugs, test gaps & quality, and code quality issues. Fix obvious bugs with regression tests; flag ambiguous issues with `# TODO(bug-bash):` comments for human review. Produce a summary table of all findings. All fixes must pass the existing test suite and linting/formatting checks without changing the project's architecture, public API surface, or dependencies.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript ~5.9 (frontend), Node 22
**Primary Dependencies**: FastAPI, React 19, Vite 7, Tailwind CSS 4, TanStack Query, Pydantic 2.x, githubkit, aiosqlite
**Storage**: SQLite with WAL mode (aiosqlite) — sessions, settings, migrations
**Testing**: pytest + pytest-asyncio (backend, ~1,400+ tests across 59 files), Vitest (frontend unit, 33 files), Playwright (frontend e2e, 9 files)
**Target Platform**: Docker Compose (Linux containers), nginx reverse proxy
**Project Type**: Web application (backend/ + frontend/)
**Performance Goals**: N/A — bug fixes must not degrade existing behavior
**Constraints**: No architecture changes, no public API changes, no new dependencies, each fix minimal and focused
**Scale/Scope**: ~90 backend source files (~15K LOC), ~87 frontend source files, ~101 test files (~29K backend test LOC)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — PASS
Feature work began with explicit specification (spec.md) containing 5 prioritized user stories (P1–P5) with Given-When-Then acceptance scenarios, clear scope boundaries (no architecture changes, no new dependencies), and measurable success criteria (SC-001 through SC-008).

### II. Template-Driven Workflow — PASS
All artifacts follow canonical templates: spec.md from spec-template, plan.md from plan-template. No custom sections added without justification.

### III. Agent-Orchestrated Execution — PASS
Workflow follows the specify → plan → tasks → implement pipeline. Each phase produces specific outputs and hands off to the next agent.

### IV. Test Optionality with Clarity — PASS
The spec **explicitly mandates tests**: FR-013 requires at least one regression test per bug fix, and SC-002 requires a 1:1 fix-to-test ratio. Tests are mandatory for this feature by specification, not by default.

### V. Simplicity and DRY — PASS
Changes are strictly scoped to minimal bug fixes. No architectural refactoring, no premature abstraction. Each fix must be the simplest correct solution. Ambiguous trade-offs are flagged, not resolved.

**GATE RESULT: ALL PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/025-bug-basher/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file
├── research.md          # Phase 0: audit methodology & tool research
├── data-model.md        # Phase 1: bug report entry, regression test, TODO flag entities
├── quickstart.md        # Phase 1: verification commands
├── contracts/           # Phase 1: output format contracts (summary table)
│   └── output-contracts.md
├── checklists/
│   └── requirements.md  # Quality checklist (completed)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # 16 API modules — audit for: auth bypasses, input validation,
│   │   │                  error handling, response consistency
│   │   ├── agents.py
│   │   ├── auth.py
│   │   ├── board.py
│   │   ├── chat.py
│   │   ├── chores.py
│   │   ├── cleanup.py
│   │   ├── health.py
│   │   ├── mcp.py
│   │   ├── metadata.py
│   │   ├── projects.py
│   │   ├── settings.py
│   │   ├── signal.py
│   │   ├── tasks.py
│   │   ├── webhooks.py
│   │   └── workflow.py
│   ├── models/          # 16 model files — audit for: validation rules, type safety,
│   │   │                  missing constraints
│   │   ├── agent.py
│   │   ├── agent_creator.py
│   │   ├── agents.py
│   │   ├── board.py
│   │   ├── chat.py
│   │   ├── chores.py
│   │   ├── cleanup.py
│   │   ├── mcp.py
│   │   ├── project.py
│   │   ├── recommendation.py
│   │   ├── settings.py
│   │   ├── signal.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── workflow.py
│   ├── services/        # 43 service files — audit for: resource leaks, race conditions,
│   │   │                  exception handling, null references
│   │   ├── agents/
│   │   ├── chores/
│   │   ├── copilot_polling/
│   │   ├── github_projects/
│   │   ├── workflow_orchestrator/
│   │   ├── ai_agent.py
│   │   ├── cache.py
│   │   ├── cleanup_service.py
│   │   ├── completion_providers.py
│   │   ├── database.py
│   │   ├── encryption.py
│   │   ├── github_auth.py
│   │   ├── github_commit_workflow.py
│   │   ├── metadata_service.py
│   │   ├── model_fetcher.py
│   │   ├── mcp_store.py
│   │   ├── session_store.py
│   │   ├── settings_store.py
│   │   ├── signal_bridge.py
│   │   ├── signal_chat.py
│   │   ├── signal_delivery.py
│   │   └── websocket.py
│   ├── middleware/       # 2 files — audit for: request handling edge cases
│   ├── prompts/         # 2 files — audit for: injection risks in prompt templates
│   ├── config.py        # Audit for: insecure defaults, missing validation
│   ├── constants.py     # Audit for: hardcoded values
│   ├── dependencies.py  # Audit for: initialization safety
│   ├── exceptions.py    # Audit for: exception hierarchy completeness
│   ├── logging_utils.py # Audit for: sensitive data in logs
│   ├── main.py          # Audit for: startup/shutdown safety
│   └── utils.py         # Audit for: BoundedDict/BoundedSet correctness
├── tests/
│   ├── conftest.py      # Audit for: mock leaks, fixture scoping
│   ├── helpers/         # Audit for: factory/mock correctness
│   ├── integration/     # 3 integration tests
│   └── unit/            # 51 unit test files
│       └── ...          # Audit for: mock leaks, meaningless assertions,
│                          untested code paths, tests passing for wrong reasons

frontend/
├── src/
│   ├── components/      # ~60 component files — audit for: XSS, unhandled errors,
│   │   │                  accessibility, state management bugs
│   │   ├── agents/
│   │   ├── auth/
│   │   ├── board/
│   │   ├── chat/
│   │   ├── chores/
│   │   ├── common/
│   │   ├── settings/
│   │   └── ui/
│   ├── hooks/           # ~20 hooks — audit for: race conditions, stale closures,
│   │                      dependency array bugs, error handling
│   ├── lib/             # 6 files — audit for: command injection, type safety
│   ├── pages/           # 2 pages — audit for: error boundaries, loading states
│   ├── services/        # API client — audit for: error handling, auth header injection
│   ├── types/           # Type definitions — audit for: missing/incorrect types
│   └── utils/           # Utility functions — audit for: edge cases
├── e2e/                 # 9 E2E tests — audit for: flaky selectors, missing assertions
└── ...config files      # Audit for: insecure build/lint config
```

**Structure Decision**: Web application layout (backend/ + frontend/). This feature does not create new directories. All changes are in-place modifications to existing files (bug fixes) plus new regression test additions in the existing test directories.

## Audit Execution Strategy

### Phase Order (by category priority)

| Phase | Category | Priority | Scope | Estimated Files |
|-------|----------|----------|-------|-----------------|
| 1 | Security Vulnerabilities | P1 | Full stack | ~20 high-priority files |
| 2 | Runtime Errors | P2 | Full stack | ~40 service/API files |
| 3 | Logic Bugs | P3 | Full stack | ~60 logic-heavy files |
| 4 | Test Gaps & Quality | P4 | Test suite | ~101 test files |
| 5 | Code Quality Issues | P5 | Full stack | All remaining files |

### Audit Approach per File

1. **Read** the entire file to understand its purpose and flow
2. **Check** each bug category (security → runtime → logic → test → quality) in order
3. **Fix** obvious bugs inline with minimal changes
4. **Add** regression test(s) for each fix in the corresponding test file
5. **Flag** ambiguous issues with `# TODO(bug-bash):` comment
6. **Record** each finding in the summary table
7. **Validate** fix by running the relevant test file(s)

### High-Priority Audit Targets

**Security (Category 1)**:
- `backend/src/api/auth.py` — OAuth flow, token handling
- `backend/src/services/github_auth.py` — GitHub authentication
- `backend/src/services/encryption.py` — Token encryption
- `backend/src/config.py` — Configuration/secrets management
- `backend/src/api/webhooks.py` — Webhook signature verification
- `backend/src/middleware/request_id.py` — Request context
- `frontend/src/services/api.ts` — API client auth headers
- `frontend/src/hooks/useAuth.ts` — Authentication state

**Runtime (Category 2)**:
- `backend/src/services/database.py` — DB connection lifecycle
- `backend/src/services/signal_bridge.py` — WebSocket connections
- `backend/src/services/signal_delivery.py` — Retry logic
- `backend/src/services/copilot_polling/` — All 8 files (async polling loops)
- `backend/src/services/github_projects/service.py` — GitHub API calls
- `backend/src/dependencies.py` — Service initialization

**Logic (Category 3)**:
- `backend/src/services/workflow_orchestrator/` — State transitions
- `backend/src/services/chores/` — Scheduling logic
- `backend/src/services/cache.py` — Cache invalidation
- `frontend/src/hooks/useProjectBoard.ts` — Board state management
- `frontend/src/components/board/` — Drag-and-drop logic

**Test Quality (Category 4)**:
- `backend/tests/conftest.py` — Mock/fixture scoping
- `backend/tests/unit/test_copilot_polling.py` — Largest test file (7,789 LOC)
- `backend/tests/unit/test_github_projects.py` — Second largest (4,037 LOC)
- All test files using `MagicMock` — Check for mock leaks

**Code Quality (Category 5)**:
- All files — Dead code, silent failures, hardcoded values

## Complexity Tracking

> No constitution violations. No complexity justification needed.
>
> This feature is scoped to minimal, focused fixes. Each change is deliberately simple —
> the constraint against architectural changes and new dependencies prevents complexity growth.
