# Implementation Plan: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Branch**: `029-chores-page-enhancements` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/029-chores-page-enhancements/spec.md`

## Summary

Enhance the existing Chores page (`ChoresPage`, `ChoresPanel`, `ChoreCard`) and its backend (`chores` table, `ChoresService`, `chores/counter.py`) with six capability tiers: (1) fix per-Chore "Every x issues" counters to query GitHub Parent Issues created since each Chore's `last_triggered_at` (not a global count), storing `execution_count` on the Chore record and using it both for tile display and trigger evaluation; (2) add a "Featured Rituals" panel above the Chore grid surfacing three highlight cards — Next Run (lowest remaining count), Most Recently Run (latest `last_triggered_at`), Most Run (highest `execution_count`); (3) make Chore definitions inline-editable with dirty-state tracking, unsaved-changes navigation guard, and PR creation on save using the existing `commit_files_workflow`; (4) add an "AI Enhance" toggle to the Chore creation/edit flow (styled like the existing `ChatToolbar` toggle) that, when OFF, preserves the user's exact chat input as the Issue Template body while still invoking the Chat Agent for metadata generation; (5) add a per-Chore "Agent Pipeline" selector (dropdown with saved pipelines + "Auto") where "Auto" resolves at runtime to the Project's active pipeline via `project_settings.assigned_pipeline_id`; (6) implement a two-step confirmation modal for new Chore creation, followed by sequential GitHub Issue creation, PR creation, and auto-merge into main using the GitHub API. The implementation extends the existing `Chore` model with `execution_count`, `ai_enhance_enabled`, and `agent_pipeline_id` fields, adds ~4 new frontend components, modifies ~8 existing components/hooks, and adds 1 new database migration.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, react-router-dom v7, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12, githubkit (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — extending `chores` table with `execution_count`, `ai_enhance_enabled`, `agent_pipeline_id`; leveraging existing `pipeline_configs` and `project_settings` tables
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers, 1024px minimum viewport width; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Featured Rituals panel loads within 2s (SC-002); counter accuracy on page load (SC-001); inline edit + PR creation under 30s (SC-003); auto-merge flow under 60s (SC-006)
**Constraints**: No new UI libraries; must not break existing Chore CRUD, trigger evaluation, or template commit flow; Agent Pipeline "Auto" must be a runtime lookup, not cached; auto-merge failures must not block local Chore persistence
**Scale/Scope**: ~4 new frontend components, ~8 modified components/hooks, 1 new migration, 2 modified backend services, 1 modified API router, 1 new API endpoint

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 17 functional requirements (FR-001–FR-017), 8 success criteria, 8 edge cases, 5 key entities, 6 assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing `ChoreCard`, `ChoresPanel`, `AddChoreModal` components; reuses `commit_files_workflow` for PR creation; reuses `ChatToolbar` AI Enhance toggle pattern; reuses existing `pipeline_configs` and `project_settings` tables for pipeline selection; no new UI libraries |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-017) and success criteria (SC-001–SC-008) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure from prior specs |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected by additive schema changes (new columns with defaults) |
| **V. Simplicity/DRY** | ✅ PASS | Reuses `commit_files_workflow` for PR creation (no new commit logic). Reuses `ChatToolbar` toggle pattern for AI Enhance (no new toggle component). Per-Chore pipeline stored as a simple `agent_pipeline_id` FK reference. Featured Rituals panel is a derived view computed from existing Chore fields (no new table). Counter fix is a query change + new `execution_count` column, not a new service. Two-step confirmation uses a single modal component with step state. Auto-merge uses existing GitHub API via `githubkit`. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/029-chores-page-enhancements/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R12)
├── data-model.md        # Phase 1: Entity extensions, types, schema changes
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: REST API endpoint contracts (new + modified)
│   └── components.md    # Phase 1: Component interface contracts (new + modified)
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── chores.py                    # MODIFIED: Add counter endpoint, inline edit save, auto-merge endpoint
│   ├── models/
│   │   └── chores.py                    # MODIFIED: Add execution_count, ai_enhance_enabled, agent_pipeline_id; add ChoreInlineUpdate
│   ├── services/
│   │   ├── chores/
│   │   │   ├── service.py               # MODIFIED: Add per-Chore counter query, inline update with PR, auto-merge
│   │   │   ├── counter.py               # MODIFIED: Fix counter to use per-Chore parent issue query bounded by last_triggered_at
│   │   │   ├── template_builder.py      # MODIFIED: Support inline edit commit (update existing template file)
│   │   │   └── chat.py                  # MODIFIED: Support metadata-only generation (AI Enhance OFF path)
│   │   └── github_commit_workflow.py    # UNCHANGED: Reused for PR creation
│   └── migrations/
│       └── 016_chores_enhancements.sql  # NEW: Add execution_count, ai_enhance_enabled, agent_pipeline_id columns
└── tests/
    └── unit/                            # Existing tests — no changes expected

frontend/
├── src/
│   ├── pages/
│   │   └── ChoresPage.tsx               # MODIFIED: Add Featured Rituals panel, unsaved-changes guard
│   ├── components/
│   │   └── chores/
│   │       ├── ChoresPanel.tsx          # MODIFIED: Wire inline editing state, dirty tracking
│   │       ├── ChoreCard.tsx            # MODIFIED: Fix counter display, add inline edit fields, AI Enhance toggle, pipeline selector
│   │       ├── AddChoreModal.tsx        # MODIFIED: Add two-step confirmation, AI Enhance toggle, pipeline selector
│   │       ├── ChoreScheduleConfig.tsx  # UNCHANGED: Existing schedule editor
│   │       ├── ChoreChatFlow.tsx        # MODIFIED: Support AI Enhance OFF path (metadata-only generation)
│   │       ├── FeaturedRitualsPanel.tsx  # NEW: Three-card panel (Next Run, Most Recently Run, Most Run)
│   │       ├── ChoreInlineEditor.tsx    # NEW: Inline editable Chore definition fields
│   │       ├── ConfirmChoreModal.tsx     # NEW: Two-step confirmation modal for new Chore creation
│   │       └── PipelineSelector.tsx      # NEW: Per-Chore Agent Pipeline dropdown (saved configs + Auto)
│   ├── hooks/
│   │   ├── useChores.ts                 # MODIFIED: Add counter query hook, inline update mutation, auto-merge mutation
│   │   └── useUnsavedChanges.ts         # NEW: Generic unsaved-changes navigation guard hook
│   ├── services/
│   │   └── api.ts                       # MODIFIED: Add chore counter, inline update, auto-merge to choresApi
│   └── types/
│       └── index.ts                     # MODIFIED: Extend Chore with execution_count, ai_enhance_enabled, agent_pipeline_id; add FeaturedRituals type
```

**Structure Decision**: Web application (frontend/ + backend/). Extends the existing chores components directory (`frontend/src/components/chores/`) and backend chores service (`backend/src/services/chores/`). New components (`FeaturedRitualsPanel`, `ChoreInlineEditor`, `ConfirmChoreModal`, `PipelineSelector`) are added to the existing `chores/` directory. The `useUnsavedChanges` hook is generic and placed in `hooks/` for reuse. No new top-level directories needed. All changes build on established patterns from the initial chores implementation (migration 010) and the pipeline system (specs 026, 028).

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Add `execution_count` column to `chores` table | Counter needs a persistent all-time execution count for "Most Run" ranking and for accurate counter reset after trigger. A simple integer column is the minimal change. | Compute from issue history (rejected: requires expensive GitHub API query on every page load; `execution_count` is O(1) to read) |
| Store `agent_pipeline_id` as nullable FK on `chores` | Per-Chore pipeline is a single reference. Null/empty means "Auto" (runtime lookup from `project_settings.assigned_pipeline_id`). Simple FK avoids a junction table. | Embedded pipeline config JSON on Chore (rejected: duplicates data, goes stale if pipeline is updated) |
| Reuse `commit_files_workflow` for inline edit PRs | The existing workflow (branch → commit → PR) is proven and handles error cases. Adding a new PR path would duplicate logic. | Direct GitHub API calls (rejected: duplicates branch/commit/PR logic already abstracted in `commit_files_workflow`) |
| Single modal with step state for two-step confirmation | One component with an internal `step` state (1 or 2) is simpler than chaining two separate modals. | Two separate modal components (rejected: requires coordination logic between modals, more code for no benefit) |
| Runtime pipeline resolution for "Auto" | Spec explicitly requires (FR-012) that "Auto" resolves at execution time. Reading `project_settings.assigned_pipeline_id` on trigger ensures current config. | Cache pipeline ID on Chore (rejected: goes stale when project pipeline changes) |
