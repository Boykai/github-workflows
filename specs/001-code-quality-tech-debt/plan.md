# Implementation Plan: Code Quality & Technical Debt — Cache Wrapper Extraction, Error Handling Consolidation & Dead Code Sweep

**Branch**: `001-code-quality-tech-debt` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-code-quality-tech-debt/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Internal backend refactoring to eliminate duplicated cache boilerplate (~80 LOC via `cached_fetch()` call-site refactoring), consolidate cycle-cache access (~7 call sites via `_cycle_cached()`), migrate 8 catch-log-raise patterns to `handle_service_error()` (~15–20 LOC), remove confirmed dead code in `cleanup_service.py` (~9 LOC), and author Spec 039 for auditable dead-code inventory. No API-visible behavioral changes. Singleton removal (Item 1.4) is explicitly deferred to a follow-up PR.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13)
**Primary Dependencies**: FastAPI 0.135+, Pydantic 2.12+, aiosqlite, githubkit 0.14+, OpenAI SDK, OpenTelemetry
**Storage**: SQLite (async via aiosqlite) — not affected by this refactoring
**Testing**: pytest with pytest-asyncio (asyncio_mode="auto"), pytest-cov (75% coverage threshold), pytest-timeout; ruff (linting); pyright (type checking); bandit (security)
**Target Platform**: Linux server (backend service)
**Project Type**: Web application (backend only — `solune/backend/`)
**Performance Goals**: N/A — pure refactoring, no performance targets; behavioral equivalence is the constraint
**Constraints**: Zero behavioral changes at API boundaries — identical cache TTLs, stale-fallback semantics, exception types, and response shapes
**Scale/Scope**: ~10 files modified, ~100+ LOC net reduction, 0 new endpoints or models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, and clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates; plan.md, research.md, data-model.md generated per template |
| III. Agent-Orchestrated Execution | ✅ PASS | speckit.plan agent produces plan artifacts; speckit.tasks will decompose into executable tasks |
| IV. Test Optionality with Clarity | ✅ PASS | Tests mandated only where spec requires (FR-005: regression test for branch_preserved path, FR-011: verification gate after each item). No blanket test mandate |
| V. Simplicity and DRY | ✅ PASS | The entire feature IS a DRY consolidation. `cached_fetch()` and `_cycle_cached()` extract repeated patterns. board.py dual-key variant stays inline if abstraction is ill-fitting (spec explicitly allows 80% coverage target) |

**Gate Result**: ✅ ALL GATES PASS — Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-code-quality-tech-debt/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output — N/A (internal refactoring, no new API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/
│   │   ├── board.py             # FR-001 (cache), FR-003 (error handling — 3 sites)
│   │   ├── projects.py          # FR-001 (cache — 4 sites)
│   │   └── workflow.py          # FR-007 (deviation comments at ~L543, ~L615)
│   ├── services/
│   │   ├── cache.py             # FR-001 (cached_fetch() already exists — call-site refactoring needed)
│   │   ├── cleanup_service.py   # FR-005 (dead code removal — lines 641–649)
│   │   ├── ai_agent.py          # FR-003 (error handling — 4 sites), FR-010 (ValueError docs)
│   │   ├── agents/
│   │   │   └── service.py       # FR-003 (error handling — 1 site, bare raise)
│   │   └── github_projects/
│   │       ├── service.py       # FR-002 (_cycle_cached()), FR-001 (cache — 1 site), FR-008 (singleton deferral at L464)
│   │       ├── pull_requests.py # FR-002 (cycle cache — 3 sites)
│   │       ├── projects.py      # FR-002 (cycle cache — 1 site)
│   │       ├── copilot.py       # FR-002 (cycle cache — 2 sites)
│   │       ├── issues.py        # FR-001 (cache — 1 site), FR-002 (cycle cache — 1 site)
│   │       └── agents.py        # FR-008 (singleton deferral)
│   ├── utils.py                 # FR-001 (cache — 1 site in resolve_repository)
│   ├── exceptions.py            # AppException hierarchy (GitHubAPIError, etc.)
│   └── logging_utils.py         # handle_service_error() — FR-003, FR-004 (error_cls extension)
└── tests/
    └── unit/
        └── test_logging_utils.py  # Existing tests for handle_service_error()
```

**Structure Decision**: Web application backend — all changes scoped to `solune/backend/src/` with tests in `solune/backend/tests/`. No frontend changes. No new files except Spec 039 directory and regression test file.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations detected. The following design decisions are documented for transparency:

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| `cached_fetch()` already exists in cache.py (L187–277) | The helper is already implemented with full stale-fallback, rate-limit handling, and data-hash comparison; work is call-site refactoring, not new abstraction | N/A — leveraging existing code |
| board.py dual-key cache sites may stay inline | Spec allows 80% coverage; forcing ill-fitting abstraction violates Principle V (Simplicity) | Force all sites into generic wrapper |
| `handle_service_error()` already has `error_cls` param | The function accepts `error_cls: type[AppException] \| None`; extension needed is relaxing the type bound to `type[Exception] \| None` to also support `ValueError` | Separate wrapper function for non-AppException types |
| Singleton removal deferred to separate PR | FR-008 explicitly blocks this; 17+ consuming files (background tasks, signal bridge, orchestrator) carry highest blast radius | Include in this PR |

## Execution Phases

### Phase A — Parallel, Low Risk (Stories 1, 2, 5)

**Items 1.1 + 1.2 + 1.5** — independent, can be developed in parallel.

| Item | Scope | Files | Est. LOC Δ |
|------|-------|-------|------------|
| 1.1: `_cycle_cached()` extraction | Add instance method to `GitHubProjectsService`, refactor 7 call sites | service.py, pull_requests.py, projects.py, copilot.py, issues.py | ~−5 |
| 1.2: Inline deviation comments | Add documentation comments at workflow.py ~L543 and ~L615 | workflow.py | ~+5 |
| 1.5: Dead code block removal | Remove unreachable `branch_in_delete` inner block (lines 641–649), add regression test | cleanup_service.py, tests/ | ~−9 |

### Phase B — Sequential, Largest Change (Story 1)

**Item 1.3: `cached_fetch()` call-site refactoring** — requires Phase A stability.

| Item | Scope | Files | Est. LOC Δ |
|------|-------|-------|------------|
| 1.3: Global cache pattern consolidation | Refactor up to 10 call sites to use existing `cached_fetch()` (target 80% coverage) | board.py, projects.py, utils.py, issues.py, service.py | ~−80 |

**Key risk**: board.py dual-key lookups + stale fallback + rate-limit classification may not fit the generic wrapper. Those instances SHOULD remain inline rather than forced into ill-fitting abstraction.

### Phase C — Sequential, Error Handling (Story 3)

**Items 1.2a–1.2d: `handle_service_error()` migration** — requires Phase A stability.

| Item | Scope | Files | Est. LOC Δ |
|------|-------|-------|------------|
| 1.2a: Extend `handle_service_error()` | Relax `error_cls` type from `type[AppException] \| None` to `type[Exception] \| None` to support ValueError | logging_utils.py | ~+3 |
| 1.2b: Migrate board.py patterns | 3 catch-log-raise sites → `handle_service_error()` | api/board.py | ~−6 |
| 1.2c: Migrate ai_agent.py patterns | 4 catch-log-raise sites → `handle_service_error()` with `error_cls=ValueError` | services/ai_agent.py | ~−8 |
| 1.2d: Migrate agents/service.py pattern | 1 bare raise → `handle_service_error()` | services/agents/service.py | ~−2 |

**Open question**: The `ai_agent.py` patterns use fragile string-based error classification ("401", "404", "Access denied"). Migration should preserve this behavior but document it as technical debt. The `error_cls` parameter type needs relaxation from `type[AppException] | None` to `type[Exception] | None` to accept `ValueError`.

### Phase D — Spec Authoring & Dead Code Sweep (Story 4)

**Item 1.6: Spec 039 authoring** — time-boxed.

| Item | Scope | Files | Est. LOC Δ |
|------|-------|-------|------------|
| 1.6a: Create `specs/039-dead-code-cleanup/` | Author formal spec documenting all dead code items from static analysis | specs/039-dead-code-cleanup/spec.md | New file |
| 1.6b: Run static analysis | `ruff check --select F401,F811` and `vulture` against `src/` | N/A (tooling output) | 0 |
| 1.6c: Execute sweep | Remove confirmed dead code from inventory (time-boxed) | Various src/ files | TBD |

### Phase E — Deferred (Separate PR)

**Item 1.4: Singleton removal** — explicitly blocked by FR-008.

- Audit all 17+ consuming files (background tasks, signal bridge, orchestrator)
- Introduce `get_github_service()` accessor pattern
- Update all affected test mocks
- **NOT part of this PR**

## Verification Gates

After every completed item:

1. `cd solune/backend && python -m pytest tests/ -x` — must be green
2. `cd solune/backend && ruff check src/` — must produce no new warnings
3. API-layer test assertions for hardcoded exception type checks — must pass unchanged (especially for Phase C error handling migration)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `cached_fetch()` doesn't fit board.py dual-key pattern | Medium | Low | Allow those sites to remain inline (80% coverage target) |
| `error_cls` type relaxation breaks existing callers | Low | Medium | Type union `type[Exception] \| None` is backward-compatible with existing `type[AppException]` usage |
| Dead code removal reveals hidden dependency | Low | High | Code inspection confirms mutual exclusivity + regression test before removal |
| Singleton deferral creates tracking gap | Low | Low | FR-008 explicitly documents follow-up scope |
| ai_agent.py ValueError migration changes API behavior | Medium | High | Explicit `error_cls=ValueError` preserves exact exception type surfaced to callers |

## Dependencies

```text
Phase A (parallel):
  Item 1.1 (_cycle_cached)      ──┐
  Item 1.2 (deviation comments)  ──├── No interdependencies
  Item 1.5 (dead code removal)   ──┘

Phase B (sequential):
  Item 1.3 (cached_fetch refactoring) ── depends on Phase A stability

Phase C (sequential):
  Items 1.2a–d (error handling)  ── depends on Phase A stability

Phase D (sequential):
  Item 1.6 (Spec 039 + sweep)  ── depends on Phase B/C completion

Phase E (deferred):
  Item 1.4 (singleton removal)  ── BLOCKED, separate PR
```
