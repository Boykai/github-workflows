# Implementation Plan: Simplify GitHub Service with githubkit v0.14.6

**Branch**: `019-githubkit-migration` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/019-githubkit-migration/spec.md`

## Summary

Replace the 5,179-line hand-rolled GitHub integration (`service.py` using raw httpx + manual retry/caching/rate-limiting + 31 GraphQL string constants) with githubkit v0.14.6, a modern async Python GitHub SDK. This eliminates ~1,500–2,000 LOC of infrastructure code (retry logic, header management, ETag caching, throttling, URL construction, response parsing) while preserving all domain-specific GraphQL queries, application-layer caching (cycle cache, in-flight coalescing, global cooldown), and externally observable behavior. The migration follows a strict five-phase rollout: Foundation → REST replacement → GraphQL simplification → Infrastructure deletion → Cleanup.

## Technical Context

**Language/Version**: Python 3.11+ (pyproject.toml targets 3.11, pyright configured for 3.12)
**Primary Dependencies**: FastAPI >=0.109.0, githubkit >=0.14.0,<0.15.0 (new), httpx >=0.26.0 (retained for non-GitHub services), Pydantic >=2.5.0, aiosqlite >=0.20.0, tenacity >=8.2.0
**Storage**: SQLite via aiosqlite (sessions, settings, metadata cache — no schema changes needed)
**Testing**: pytest + pytest-asyncio (asyncio_mode = "auto"), 1,411+ tests across 48 unit test files
**Target Platform**: Linux server (Docker via docker-compose.yml)
**Project Type**: Web application (FastAPI backend + React frontend)
**Performance Goals**: Maintain current GitHub API throughput (~5,000 req/hour rate limit compliance)
**Constraints**: Single-threaded asyncio execution model, per-user token-based authentication, preview API compatibility for Sub-Issues and Copilot assignment
**Scale/Scope**: 5,179 LOC in service.py, 927 LOC in graphql.py, 313 LOC in github_auth.py — ~6,752 LOC total in target files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅
- spec.md exists with 6 prioritized user stories (P1, P1, P2, P2, P2, P3)
- Each story has Given-When-Then acceptance scenarios
- Scope boundaries clearly defined (GitHub service only; signal services, chat persistence out of scope)
- Checklist (`checklists/requirements.md`) validates completeness

### Principle II: Template-Driven Workflow ✅
- This plan follows the canonical `plan-template.md`
- Research, data model, contracts, and quickstart artifacts follow standard structure
- All artifacts in `specs/019-githubkit-migration/`

### Principle III: Agent-Orchestrated Execution ✅
- `speckit.specify` completed spec.md → `speckit.plan` (this phase) → `speckit.tasks` next
- Each agent has clear input/output boundaries
- Plan produces: research.md, plan.md, data-model.md, contracts/, quickstart.md

### Principle IV: Test Optionality with Clarity ✅
- Tests are required: the spec explicitly mandates "all existing pytest tests must pass after mock updates"
- Test mock migration is a dedicated concern (FR-013)
- No TDD approach specified; test updates follow implementation changes

### Principle V: Simplicity and DRY ✅
- Migration replaces ~1,500–2,000 LOC of infrastructure with SDK calls — net simplification
- BoundedDict client pool reuses existing utility (no new abstraction)
- RateLimitState adapter is a thin dataclass (minimal new code)
- No premature abstractions; each phase delivers concrete LOC reduction
- Complexity tracking below documents justified additions

## Project Structure

### Documentation (this feature)

```text
specs/019-githubkit-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output — technical decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — developer guide
├── contracts/           # Phase 1 output — internal API contracts
│   ├── client-factory.md
│   └── rate-limit-adapter.md
├── checklists/
│   └── requirements.md  # Pre-existing spec quality checklist
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                              # Dep changes: +githubkit, pin httpx
├── src/
│   ├── services/
│   │   ├── github_projects/
│   │   │   ├── __init__.py                     # Add GitHubClientFactory export
│   │   │   ├── service.py                      # Major refactor (~5,179 LOC → ~3,200–3,700 LOC)
│   │   │   ├── graphql.py                      # Minor cleanup (~927 LOC → ~900 LOC)
│   │   │   └── client_factory.py               # NEW: GitHubClientFactory + BoundedDict pool
│   │   ├── github_auth.py                      # OAuth migration (~313 LOC → ~270 LOC)
│   │   ├── github_commit_workflow.py           # Update to use new service API (185 LOC)
│   │   └── copilot_polling/
│   │       └── polling_loop.py                 # Update rate limit access pattern
│   ├── models/
│   │   └── rate_limit.py                       # NEW: RateLimitState dataclass
│   ├── dependencies.py                         # Update service initialization (137 LOC)
│   └── utils.py                                # No changes (BoundedDict reused as-is)
├── tests/
│   └── unit/                                   # Mock migration: httpx → githubkit
└── docs/
    ├── architecture.md                         # Update GitHub integration section
    └── configuration.md                        # Update configuration reference
```

**Structure Decision**: Existing web application structure (backend/frontend) preserved. New files are minimal: `client_factory.py` (~80 LOC) for the client pool/factory, `rate_limit.py` (~30 LOC) for the adapter dataclass. All other changes are modifications to existing files.

## Phase Execution Plan

### Phase 1: Foundation (no behavior changes)

**User Story**: Story 1 — Foundation: Add githubkit and Client Factory (P1)
**Estimated LOC Change**: +120 new, –0 removed (additive only)

| Step | File | Change | Risk |
|------|------|--------|------|
| 1.1 | `pyproject.toml` | Add `githubkit>=0.14.0,<0.15.0` to dependencies | Low — additive |
| 1.2 | `src/models/rate_limit.py` | Create `RateLimitState` dataclass | Low — new file |
| 1.3 | `src/services/github_projects/client_factory.py` | Create `GitHubClientFactory` with `BoundedDict` pool, rate limit event hook | Medium — new integration point |
| 1.4 | `src/services/github_projects/__init__.py` | Export `GitHubClientFactory` | Low — additive |
| 1.5 | `src/dependencies.py` | Register `GitHubClientFactory` on `app.state` | Low — follows existing pattern |

**Gate**: All existing tests pass unchanged. `GitHubClientFactory` has its own unit tests.

### Phase 2: Replace REST API Calls (~600–800 LOC eliminated)

**User Story**: Story 2 — Replace REST API Call Sites (P1)
**Estimated LOC Change**: –600 to –800 net

| Step | File | Change | Risk |
|------|------|--------|------|
| 2.1 | `service.py` | `create_issue()` → `github.rest.issues.create(...)` | Medium — high-value method |
| 2.2 | `service.py` | `update_issue_body()` → `github.rest.issues.update(...)` | Low |
| 2.3 | `service.py` | `update_issue_state()` → `github.rest.issues.update(...)` | Low |
| 2.4 | `service.py` | `assign_issue()` → `github.rest.issues.add_assignees(...)` | Low |
| 2.5 | `service.py` | `create_issue_comment()` → `github.rest.issues.create_comment(...)` | Low |
| 2.6 | `service.py` | `get_pr_changed_files()` → `github.rest.pulls.list_files(...)` with pagination | Medium — pagination change |
| 2.7 | `service.py` | `request_copilot_review()` → `github.rest.pulls.request_reviewers(...)` | Low |
| 2.8 | `service.py` | `delete_branch()` → `github.rest.git.delete_ref(...)` | Low |
| 2.9 | `service.py` | `mark_pr_ready_for_review()` — keep GraphQL (no REST equivalent) | N/A |
| 2.10 | `service.py` | `merge_pull_request()` → `github.rest.pulls.merge(...)` | Medium — critical operation |
| 2.11 | `service.py` | `update_pr_base()` → `github.rest.pulls.update(...)` | Low |
| 2.12 | `service.py` | `link_pull_request_to_issue()` — remains REST but uses `github.request()` | Low |
| 2.13 | `service.py` | `get_directory_contents()` → `github.rest.repos.get_content(...)` | Low |
| 2.14 | `service.py` | `get_file_content()` → `github.rest.repos.get_content(...)` | Low |
| 2.15 | `service.py` | `get_repository_info()` — keep GraphQL | N/A |
| 2.16 | `service.py` | `create_sub_issue()` → `github.request("POST", ...)` (preview API) | Low |
| 2.17 | `service.py` | `get_sub_issues()` → `github.request("GET", ...)` (preview API) | Low |
| 2.18 | `service.py` | `http_get()` → `github.request("GET", ...)` | Medium — public method signature change |
| 2.19 | `service.py` | `_search_open_prs_for_issue_rest()` → `github.rest.search.issues_and_pull_requests(...)` | Medium |
| 2.20 | `service.py` | `_add_issue_to_project_rest()` → `github.request("POST", ...)` | Low |
| 2.21 | `service.py` | `_assign_copilot_rest()` → `github.request("POST", ...)` | Low |
| 2.22 | `service.py` | `get_pr_timeline_events()` → `github.request("GET", ...)` | Low |
| 2.23 | `service.py` | `has_copilot_reviewed_pr()` → `github.rest.pulls.list_reviews(...)` | Low |
| 2.24 | `service.py` | Migrate `__init__()` to accept `GitHubClientFactory` | Medium — constructor change |

**Gate**: All existing tests pass with updated mocks. No behavioral changes.

### Phase 3: Simplify GraphQL Layer (~200 LOC eliminated)

**User Story**: Story 3 — Simplify the GraphQL Layer (P2)
**Estimated LOC Change**: –200 net

| Step | File | Change | Risk |
|------|------|--------|------|
| 3.1 | `service.py` | Replace `_graphql()` method with `github.graphql(query, variables=...)` | High — core infrastructure change |
| 3.2 | `service.py` | Remove ETag cache fields and logic from `__init__()` | Low — dead code after 3.1 |
| 3.3 | `service.py` | Preserve in-flight coalescing (`_inflight_graphql`) as app-layer logic | Medium — must not regress |
| 3.4 | `service.py` | Preserve cycle cache as app-layer logic | Low — untouched |
| 3.5 | `service.py` | Consolidate all `_with_fallback()` usage | Low |

**Gate**: All GraphQL-dependent tests pass. ETag caching now handled by githubkit.

### Phase 4: Migrate OAuth + Delete Infrastructure (~450 LOC eliminated)

**User Story**: Story 4 — Migrate OAuth (P2) + Story 5 — Delete Deprecated Infrastructure (P3)
**Estimated LOC Change**: –400 to –450 net

| Step | File | Change | Risk |
|------|------|--------|------|
| 4.1 | `github_auth.py` | Replace `exchange_code_for_token()` with githubkit OAuth | Medium |
| 4.2 | `github_auth.py` | Replace `get_github_user()` with `github.rest.users.get_authenticated()` | Low |
| 4.3 | `github_auth.py` | Replace `refresh_token()` with githubkit token refresh | Medium |
| 4.4 | `github_auth.py` | Remove `self._client = httpx.AsyncClient(...)` | Low |
| 4.5 | `service.py` | Delete `_request_with_retry()` (~150 LOC) | Low — all callers migrated |
| 4.6 | `service.py` | Delete `_build_headers()` | Low |
| 4.7 | `service.py` | Delete `_extract_rate_limit_headers()` | Low |
| 4.8 | `service.py` | Delete `get_last_rate_limit()` / `clear_last_rate_limit()` | Medium — polling loop must use adapter |
| 4.9 | `service.py` | Delete `_parse_retry_after_seconds()`, `_is_secondary_limit()` | Low |
| 4.10 | `service.py` | Delete `_apply_global_cooldown()`, `_respect_global_cooldown()` | Low |
| 4.11 | `service.py` | Remove ETag cache fields, throttling fields from `__init__()` | Low |
| 4.12 | `copilot_polling/polling_loop.py` | Migrate `get_last_rate_limit()` → `RateLimitState` adapter | Medium |

**Gate**: Full test suite passes. No references to deleted methods in production code.

### Phase 5: Cleanup (parallel with Phase 4)

**User Story**: Story 5 — Delete Deprecated Infrastructure and Clean Up (P3) + Story 6 — Rate Limit Visibility Adapter (P2)
**Estimated LOC Change**: –50 net

| Step | File | Change | Risk |
|------|------|--------|------|
| 5.1 | `graphql.py` | Remove `MAX_RETRIES`, `INITIAL_BACKOFF_SECONDS`, `MAX_BACKOFF_SECONDS` | Low |
| 5.2 | `graphql.py` | Remove `GITHUB_GRAPHQL_URL` (githubkit handles endpoint) | Low |
| 5.3 | `docs/architecture.md` | Update GitHub integration section | Low |
| 5.4 | `docs/configuration.md` | Update configuration reference | Low |
| 5.5 | Tests | Update all httpx mocks → githubkit mocks | High — many test files |
| 5.6 | `dependencies.py` | Update service initialization for new factory | Low |

**Gate**: Full test suite passes. `ruff check` clean. `pyright` clean. Documentation accurate.

## Dependency Graph

```
Phase 1 (Foundation)
    ├── Phase 2 (REST replacement) ──┐
    │                                 ├── Phase 4 (OAuth + Infrastructure deletion)
    └── Phase 3 (GraphQL simplify) ──┘          │
                                                 └── Phase 5 (Cleanup + docs)
```

- Phase 1 must complete first (all other phases depend on the client factory).
- Phases 2 and 3 can proceed in parallel after Phase 1.
- Phase 4 requires Phases 2 and 3 (deletes infrastructure they depend on during transition).
- Phase 5 runs parallel with or after Phase 4.

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| githubkit API doesn't match expected interface | High | Low | Pin version, verify against docs before each phase |
| Test mock migration breaks test isolation | Medium | Medium | Migrate mocks incrementally per phase, run full suite after each |
| Rate limit adapter misses edge cases | Medium | Low | Compare adapter output vs raw headers in integration tests |
| Preview API endpoints change behavior | Low | Low | Generic `github.request()` allows URL/header customization |
| Connection pool exhaustion under load | Medium | Low | BoundedDict cap at 50 + LRU eviction prevents unbounded growth |
| Signal services break from httpx changes | Low | Low | httpx remains a transitive dependency; signal services unchanged |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New `client_factory.py` file | Separates client lifecycle management from business logic in service.py | Embedding in service.py would add complexity to an already-large file (5,179 LOC) |
| New `rate_limit.py` model | Decouples rate limit state from service internals | Inline dict (current approach) lacks type safety and documentation |
| httpx retained as direct dependency | Signal services (signal_bridge.py, signal_delivery.py) need httpx for non-GitHub HTTP calls | Replacing with aiohttp is out of scope for this migration |
