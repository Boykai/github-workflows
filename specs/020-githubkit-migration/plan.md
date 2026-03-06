# Implementation Plan: Simplify GitHub Service with githubkit

**Branch**: `020-githubkit-migration` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/020-githubkit-migration/spec.md`

## Summary

Replace 6,600 LOC of hand-rolled GitHub API infrastructure (httpx + manual retry/cache/throttle/OAuth) with githubkit v0.14.6, a modern async Python GitHub SDK. The SDK provides built-in retry, HTTP caching, throttling, typed REST methods, and OAuth flow — eliminating ~1,500-2,000 LOC while preserving all 85 business-logic methods and domain-specific optimizations (cycle cache, inflight coalescing, Projects V2 GraphQL queries).

## Technical Context

**Language/Version**: Python 3.11+ (pyproject.toml targets 3.11, pyright targets 3.12)
**Primary Dependencies**: FastAPI, githubkit (new, replacing httpx), github-copilot-sdk, aiosqlite, pydantic 2.x
**Storage**: SQLite with WAL mode (aiosqlite) — sessions, settings, migrations
**Testing**: pytest + pytest-asyncio + pytest-cov
**Target Platform**: Linux server (Docker container)
**Project Type**: Web application (FastAPI backend + React frontend) — this feature is backend-only
**Performance Goals**: Match current retry/throttle behavior; ≥500ms inter-call spacing via SDK throttler
**Constraints**: No user-visible behavior changes; all existing tests must pass with only mock-target updates
**Scale/Scope**: 4 backend files affected (~6,600 LOC total), 20+ REST call sites, 31 GraphQL queries/mutations, ~15 test files with httpx mocks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 5 prioritized user stories, acceptance scenarios, clarifications |
| II. Template-Driven Workflow | ✅ PASS | Following canonical plan template |
| III. Agent-Orchestrated Execution | ✅ PASS | Following specify → plan → tasks → implement pipeline |
| IV. Test Optionality | ✅ PASS | Tests not explicitly requested; existing tests updated for mock-target changes only |
| V. Simplicity and DRY | ✅ PASS | Core goal is simplification — replacing custom infrastructure with SDK eliminates duplication |

**Gate result**: PASS — no violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/020-githubkit-migration/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0: SDK research findings
├── data-model.md        # Phase 1: Entity mapping (client factory, exception types)
├── quickstart.md        # Phase 1: Migration quickstart guide
├── contracts/           # Phase 1: API contracts (internal service interface)
│   └── api-contracts.md
├── checklists/
│   └── requirements.md  # Quality checklist (complete)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/
│   │   ├── github_projects/
│   │   │   ├── __init__.py        # GitHubClientFactory (new), singleton
│   │   │   ├── service.py         # GitHubProjectsService (refactored, ~3,500 LOC target)
│   │   │   └── graphql.py         # GraphQL queries/mutations (cleanup only)
│   │   ├── github_auth.py         # OAuth flow (simplified via SDK)
│   │   └── github_commit_workflow.py  # Commit pipeline (updated imports)
│   ├── dependencies.py            # Service initialization (updated)
│   └── ...
└── tests/
    └── unit/                      # Mock-target updates for githubkit
```

**Structure Decision**: Existing web application layout. This feature modifies only the backend `services/` layer. No new directories needed — the client factory goes in the existing `__init__.py`. No frontend changes.

## Complexity Tracking

> No constitution violations to justify. The migration simplifies the codebase.
