# Implementation Plan: Preserve Full User-Provided GitHub Issue Description Without Truncation

**Branch**: `014-preserve-issue-description` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-preserve-issue-description/spec.md`

## Summary

Audit and harden the chat-to-GitHub-issue pipeline so that user-provided issue descriptions of any length (up to the GitHub API 65,536-character limit) are preserved verbatim — including all markdown formatting, Unicode, and special characters — from chat input through to the created GitHub Issue body. Remove or bypass any truncation, summarisation, or length-capping that currently affects the description destined for the API `body` field, add an explicit user notification when the description exceeds the API limit, and add unit/integration tests at common truncation boundaries to verify end-to-end content fidelity.

## Technical Context

**Language/Version**: Python 3.11+ (backend; dev environment targets 3.12), TypeScript 5.4 / Node 20 (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, httpx (backend); React 18, TanStack Query v5 (frontend)
**Storage**: SQLite (aiosqlite, WAL mode) — in-memory for tests; in-memory dicts for proposals/recommendations (MVP)
**Testing**: pytest 7.4+ / pytest-asyncio 0.23+ (backend), Vitest 4.0+ / @testing-library/react (frontend)
**Target Platform**: Linux server (backend), Modern browsers (frontend)
**Project Type**: web (backend + frontend)
**Performance Goals**: No additional latency; issue creation response time unchanged for descriptions up to 65,536 characters
**Constraints**: GitHub REST API hard limit of 65,536 characters for the `body` field; no new dependencies
**Scale/Scope**: ~6 backend files modified, ~3 frontend files modified; ~4 new test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with 4 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility agent model; outputs are well-defined markdown documents |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly required by spec (FR-009, SC-002, SC-005); boundary tests mandated at 256, 1024, 4096, 65536 characters |
| V. Simplicity and DRY | ✅ PASS | Changes are surgical — remove/relax existing constraints rather than adding new abstractions; reuse existing service layer |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/014-preserve-issue-description/
├── plan.md              # This file
├── research.md          # Phase 0: Pipeline audit findings and decisions
├── data-model.md        # Phase 1: Entity model for description passthrough
├── quickstart.md        # Phase 1: Developer quickstart for testing changes
├── contracts/           # Phase 1: API contract changes
│   └── issue-creation-contract.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── chat.py              # Chat endpoint — proposal confirmation creates issues
│   │   └── workflow.py           # Workflow endpoint — recommendation confirmation creates issues
│   ├── models/
│   │   └── recommendation.py     # AITaskProposal, IssueRecommendation, ProposalConfirmRequest models
│   ├── services/
│   │   ├── ai_agent.py           # AI recommendation generation, title truncation
│   │   ├── github_projects/
│   │   │   └── service.py        # GitHub REST API — create_issue(body=...)
│   │   ├── signal_chat.py        # Signal chat pipeline — issue body construction
│   │   └── workflow_orchestrator/
│   │       └── orchestrator.py   # format_issue_body(), create_issue_from_recommendation()
│   └── prompts/
│       └── issue_generation.py   # LLM system prompt (already preserves details)
└── tests/
    └── unit/
        ├── test_api_chat.py      # Chat API tests
        └── test_api_workflow.py   # Workflow API tests

frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       └── IssueRecommendationPreview.tsx  # Issue preview UI
│   ├── hooks/
│   │   └── useChat.ts            # Chat state management
│   ├── services/
│   │   └── api.ts                # API client
│   └── types/
│       └── index.ts              # Type definitions
└── src/test/
    └── setup.ts                  # Test setup with createMockApi()
```

**Structure Decision**: Web application (backend + frontend split). The repository already uses this structure. Changes are scoped to existing files — no new modules or packages are introduced.

## Complexity Tracking

> No constitution violations to justify. All principles are satisfied.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts trace back to spec.md requirements (FR-001 through FR-009, SC-001 through SC-006) |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly required by specification — boundary tests at 256, 1024, 4096, 65536 chars mandated by SC-002 |
| V. Simplicity and DRY | ✅ PASS | Changes are surgical — fix off-by-one, add one validation check, add one constant; no new abstractions or patterns introduced |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
