# Implementation Plan: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Branch**: `030-chat-pipeline-config` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-chat-pipeline-config/spec.md`

## Summary

Wire the Project page's currently selected Agent Pipeline configuration into the chat's issue-creation flow so that every GitHub Issue created via chat automatically inherits the active pipeline. The backend's `confirm_proposal` endpoint in `chat.py` will resolve the project-level `assigned_pipeline_id` (already stored in `project_settings` by the Projects page) and convert it to `agent_mappings` before creating sub-issues — replacing the current per-user `load_user_agent_mappings()` lookup with a project-wide pipeline-first resolution that falls back to user mappings and then defaults. The frontend chat confirmation will surface the applied pipeline name, and the chat UI will warn when no pipeline is selected on the Project page. A new `useSelectedPipeline` hook provides a shared, cache-friendly way for both the Projects page and chat to read the current assignment.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — existing `project_settings` table (`assigned_pipeline_id` column), existing `pipeline_configs` table
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Pipeline resolution at issue-creation time < 100ms; pipeline assignment sync between Project page and chat < 2s (React Query staleTime); chat confirmation message renders pipeline name inline
**Constraints**: No new libraries; reuse existing `pipelinesApi`, `project_settings` table, and `WorkflowConfiguration` model; pipeline-to-agent-mappings conversion must be backend-side to avoid stale-state bugs; existing per-user mapping flow must remain as fallback
**Scale/Scope**: ~2 modified backend files, ~1 new backend utility function, ~3 modified frontend files, ~1 new frontend hook, ~1 new frontend component

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 9 functional requirements, 5 success criteria, edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing pipeline assignment infrastructure (`assigned_pipeline_id` already stored); reuses `pipelinesApi`, `WorkflowConfiguration`, and TanStack Query patterns; no new libraries required |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-009) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `project_settings.assigned_pipeline_id` storage, existing `pipeline_configs` table, existing `pipelinesApi` client, existing `AgentPresetSelector` persistence pattern. Pipeline-to-mappings conversion is a single utility function in `config.py`. Frontend hook (`useSelectedPipeline`) wraps an existing React Query call. Chat warning is a lightweight inline banner. No new database tables, no new API routes for pipeline assignment (existing `GET /PUT /pipelines/{projectId}/assignment` endpoints used). |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-chat-pipeline-config/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: Entity definitions, types
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: Backend API contract changes
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── chat.py                          # MODIFIED: Resolve project pipeline in confirm_proposal
│   └── services/
│       └── workflow_orchestrator/
│           └── config.py                    # MODIFIED: Add resolve_project_pipeline_mappings() + load_pipeline_as_agent_mappings()

frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── TaskPreview.tsx              # MODIFIED: Display applied pipeline name in confirmation
│   │       └── PipelineWarningBanner.tsx    # NEW: Inline warning when no pipeline selected
│   ├── hooks/
│   │   └── useSelectedPipeline.ts           # NEW: Shared hook for reading project pipeline assignment
│   ├── pages/
│   │   └── ProjectsPage.tsx                 # MODIFIED: Use useSelectedPipeline hook (optional refactor for DRY)
│   ├── services/
│   │   └── api.ts                           # MODIFIED: Extend ProposalConfirmRequest type (if pipeline_id passed)
│   └── types/
│       └── index.ts                         # MODIFIED: Extend AITaskProposal with pipeline_name field
```

**Structure Decision**: Web application (frontend/ + backend/). All changes extend existing directories and files. One new frontend hook (`useSelectedPipeline.ts`) and one new frontend component (`PipelineWarningBanner.tsx`). Backend changes are concentrated in two existing files (`chat.py` and `config.py`). No new database tables or migrations — reuses existing `project_settings.assigned_pipeline_id` column and `pipeline_configs` table.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Backend-side pipeline resolution | Pipeline-to-mappings conversion happens in `confirm_proposal` (backend) to avoid stale-state bugs where frontend sends a pipeline ID that was deleted between selection and confirmation | Frontend-side resolution (rejected: race condition if pipeline deleted between chat session start and confirmation; backend has authoritative DB access) |
| Project-level pipeline first, user-level fallback | `resolve_project_pipeline_mappings()` checks `assigned_pipeline_id` first, then falls back to `load_user_agent_mappings()`, then defaults — preserving backward compatibility | Replace user mappings entirely (rejected: would break existing per-user overrides; users who configured agent mappings via Settings should retain their customization until the project pipeline is explicitly set) |
| Reuse existing assignment API | Frontend reads pipeline assignment via existing `GET /pipelines/{projectId}/assignment` endpoint — no new API required | Add a dedicated chat pipeline endpoint (rejected: duplicates existing functionality; YAGNI; the assignment endpoint already returns exactly what the chat needs) |
