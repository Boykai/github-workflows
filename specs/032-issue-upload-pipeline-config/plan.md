# Implementation Plan: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Branch**: `032-issue-upload-pipeline-config` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/032-issue-upload-pipeline-config/spec.md`

## Summary

Add a cohesive form section to the Projects page that allows users to paste or upload a GitHub Parent Issue description (Markdown or plain text) and select an Agent Pipeline Config from a dynamically populated dropdown, then launch the pipeline in a single action. The frontend `ProjectIssueLaunchPanel` component implements the form with a multi-line textarea, file upload (.md/.txt), native `<select>` pipeline selector, real-time inline validation, and a submit button with loading/success/error states. The backend `POST /pipelines/{projectId}/launch` endpoint receives the `PipelineIssueLaunchRequest` (issue description + pipeline ID), creates a GitHub Issue, converts the pipeline config into agent mappings, adds the issue to the project board, creates per-agent sub-issues, and returns a `WorkflowResult` with the issue URL and status. No new database tables or API routes are needed — the feature builds entirely on the existing `pipeline_configs` table, `pipelinesApi` client, and `WorkflowConfiguration` pipeline execution infrastructure.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — existing `pipeline_configs` table, existing `project_settings` table (`assigned_pipeline_id` column)
**Testing**: Vitest 4 + Testing Library with happy-dom (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Form renders < 100ms; pipeline config dropdown populates within staleTime (60s cache); pipeline launch completes and returns `WorkflowResult` within 5s; file upload reads into textarea within 2s
**Constraints**: No new libraries; reuse existing `pipelinesApi`, `pipeline_configs` table, and `WorkflowConfiguration` model; issue description capped at 65,536 characters (frontend) and validated against `GITHUB_ISSUE_BODY_MAX_LENGTH` (backend); file upload limited to `.md` and `.txt` extensions; submit button disabled during in-flight mutation to prevent duplicates
**Scale/Scope**: ~1 new frontend component (`ProjectIssueLaunchPanel`), ~0 new backend files (existing `POST /pipelines/{projectId}/launch` endpoint), ~2 modified frontend files (`ProjectsPage.tsx`, `types/index.ts`); 0 new database migrations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 15 functional requirements (FR-001–FR-015), 7 success criteria, edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing pipeline infrastructure (`pipeline_configs` table, `pipelinesApi` client, `POST /launch` endpoint); reuses TanStack Query, `useMutation`, native HTML form elements; no new libraries or database tables |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-015); data-model.md maps entities to spec Key Entities; contracts/ maps endpoints to functional requirements |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `pipeline_configs` table, existing `pipelinesApi.list()` and `pipelinesApi.launch()` API client methods, existing `PipelineIssueLaunchRequest` model, existing `WorkflowResult` response model. `ProjectIssueLaunchPanel` is a self-contained composable component with no external state management beyond React Query. No new database tables, no new API routes, no new backend models. Pipeline selection uses a native `<select>` element — no custom dropdown library needed. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/032-issue-upload-pipeline-config/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: Entity definitions, types, state flow
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: Backend API contract (launch endpoint)
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
│   │   └── pipelines.py                     # EXISTING: POST /{project_id}/launch endpoint (no changes needed)
│   ├── models/
│   │   └── pipeline.py                      # EXISTING: PipelineIssueLaunchRequest, PipelineConfig models
│   └── services/
│       ├── pipelines/
│       │   └── service.py                   # EXISTING: PipelineService (CRUD + assignment)
│       └── workflow_orchestrator/
│           └── orchestrator.py              # EXISTING: WorkflowOrchestrator (issue creation, sub-issue dispatch)

frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       └── ProjectIssueLaunchPanel.tsx   # NEW: Form component (textarea + file upload + pipeline select + submit)
│   ├── pages/
│   │   └── ProjectsPage.tsx                 # MODIFIED: Integrate ProjectIssueLaunchPanel into page layout
│   ├── services/
│   │   └── api.ts                           # EXISTING: pipelinesApi.list(), pipelinesApi.launch() (no changes needed)
│   └── types/
│       └── index.ts                         # EXISTING: PipelineIssueLaunchRequest, WorkflowResult types
```

**Structure Decision**: Web application (frontend/ + backend/). The feature adds one new frontend component (`ProjectIssueLaunchPanel.tsx`) and modifies one existing page (`ProjectsPage.tsx`) to render it. The backend already exposes all required API endpoints — `GET /pipelines/{projectId}` for listing configs, `POST /pipelines/{projectId}/launch` for executing the pipeline with an issue description. No new backend files, no new database tables, no new migrations.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Reuse existing `POST /launch` endpoint | The backend already implements the full pipeline launch flow: validate inputs, fetch pipeline config, create GitHub issue, create sub-issues, enqueue for blocking. No new API needed. | Create a dedicated "upload issue" endpoint (rejected: duplicates existing launch logic; YAGNI) |
| Native `<select>` for pipeline dropdown | Simple, accessible, no external library needed. Matches existing form patterns in the codebase (e.g., `AddChoreModal`). | Custom dropdown component (rejected: adds complexity; native select meets all requirements including keyboard navigation and screen reader support) |
| Client-side file reading only | File content is read via `File.text()` and placed into the textarea. No server-side file storage needed — the issue description is submitted as text. | Server-side file upload (rejected: unnecessary round-trip; file content is just text that goes into the textarea) |
| Single composable component | `ProjectIssueLaunchPanel` encapsulates all form state, validation, and submission logic. The parent `ProjectsPage` only passes pipeline data and handles the `onLaunched` callback. | Split into multiple components (rejected: the form is a single cohesive unit; splitting would require prop drilling or context for shared state) |
