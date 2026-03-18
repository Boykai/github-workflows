# Research: Debug & Fix Apps Page — New App Creation UX

**Feature**: 051-app-creation-ux | **Date**: 2026-03-18 | **Status**: Complete

## Research Tasks

### R1: Template File Error Handling — Current Behavior and Fix Strategy

**Context**: `build_template_files()` in `solune/backend/src/services/template_files.py` silently skips files that fail to read.

**Findings**:
- The function iterates through `.github/` and `.specify/` directories using `rglob("*")`
- When a file fails to read (e.g., encoding issues), it logs a warning and continues (`continue` statement)
- Return type is `list[dict[str, str]]` — a flat list of `{"path": ..., "content": ...}` dicts
- **No warnings are returned to the caller** — the function signature has no mechanism for it
- A memory note confirms the function was updated to return `tuple[list[dict], list[str]]` (files, warnings) — this may already be done on the current branch

**Decision**: Change return type to `tuple[list[dict[str, str]], list[str]]` — returning `(files, warnings)`. Collect failed file paths in a warnings list instead of silently skipping. All callers (`create_app_with_new_repo`) must unpack both values.

**Rationale**: Maintains backward compatibility at the call site with a minor signature change. Warning propagation uses the existing `App.warnings` transient field already established for Azure secret failures.

**Alternatives Considered**:
1. *Raise exception on any failure* — Rejected: too aggressive; one broken template file shouldn't block entire app creation
2. *Return a `TemplateResult` dataclass* — Rejected: overkill for a simple `(files, warnings)` tuple; YAGNI

---

### R2: Branch-Readiness Polling — Exponential Backoff Strategy

**Context**: Current poll: 5 retries × 1s linear = 5s max. Spec requires ~10 retries × exponential backoff ≈ 15s max.

**Findings**:
- Current code in `create_app_with_new_repo()` (lines ~380–400) uses `asyncio.sleep(1)` between retries
- GitHub repo creation is asynchronous — the default branch may not be available immediately
- Under GitHub load, 5 seconds is insufficient
- The `tenacity` library (already a dependency: `tenacity>=9.1.0`) provides retry/backoff decorators

**Decision**: Replace manual retry loop with 10 retries using exponential backoff: `1s, 1s, 2s, 2s, 3s, 3s, 4s` pattern (approximately). Total max wait ≈ 15 seconds. Keep inline retry logic (no tenacity decorator) for clarity and testability.

**Rationale**: Exponential backoff is standard for external API polling. 15 seconds covers typical GitHub propagation delays. Keeping it inline (not tenacity) avoids decorator complexity in an async context where the retry logic is already straightforward.

**Alternatives Considered**:
1. *Use `tenacity` retry decorator* — Rejected: adds decorator indirection to a simple loop; the function already has complex control flow
2. *Fixed 2s interval × 8 retries = 16s* — Rejected: wastes time on fast operations; exponential backoff adapts better

---

### R3: Parent Issue Creation — Wiring Existing Primitives

**Context**: All building blocks exist but are never called from app creation.

**Findings**:
- `GitHubProjectsService.create_issue()` (in `github_projects/issues.py`) — creates a GitHub issue via REST API
- `append_tracking_to_body()` (in `agent_tracking.py`) — appends agent tracking table to issue body
- `create_all_sub_issues()` (in `orchestrator.py`) — creates sub-issues per agent stage
- `ensure_polling_started()` (in `copilot_polling/__init__.py`) — starts the polling loop
- `_create_parent_issue_sub_issues()` (in `api/tasks.py`) — reference pattern for full flow
- `WorkflowContext` requires: `issue_id`, `issue_number`, `project_item_id`, `owner`, `repo`, `access_token`, `project_id`

**Decision**: Wire these existing functions into `create_app_with_new_repo()` as a new private function `_create_app_parent_issue()`. Follow the pattern in `_create_parent_issue_sub_issues()`:
1. Load pipeline config from `pipeline_id`
2. Create issue with tracking table body
3. Create sub-issues via orchestrator
4. Start polling via `ensure_polling_started()`
5. Store `parent_issue_number` and `parent_issue_url` on App record
6. Wrap entire flow in try/except — failure adds warning, does not block

**Rationale**: Reuses all existing primitives — no new abstractions. Best-effort pattern matches existing Azure secret storage pattern in the same function.

**Alternatives Considered**:
1. *Create a dedicated service class for pipeline launch* — Rejected: YAGNI; a private function in app_service.py suffices
2. *Background task queue (Celery/etc.)* — Rejected: way too heavy; the operation is fast and can be awaited inline

---

### R4: Database Migration Strategy — SQLite Column Addition

**Context**: Need to add `parent_issue_number` (INTEGER) and `parent_issue_url` (TEXT) to the `apps` table.

**Findings**:
- SQLite supports `ALTER TABLE ... ADD COLUMN` for nullable columns without defaults — no table recreation needed
- Previous migrations (028) used table recreation for CHECK constraint changes
- New columns are nullable with no constraints — simple ALTER TABLE is safe
- Migration numbering: next is `030` (029 exists for pipeline state persistence)

**Decision**: Use simple `ALTER TABLE apps ADD COLUMN` statements. No table recreation needed since:
- Both columns are nullable (no NOT NULL constraint)
- No CHECK constraints on these columns
- No foreign key changes

**Rationale**: Simplest possible migration. ALTER TABLE ADD COLUMN is the SQLite-idiomatic approach when no constraints need modifying.

**Alternatives Considered**:
1. *Full table recreation (028 pattern)* — Rejected: unnecessary complexity for simple nullable column additions
2. *Store in a separate `app_parent_issues` table* — Rejected: 1:1 relationship, denormalization is simpler and matches existing pattern

---

### R5: Pipeline Presets Source — Frontend Dropdown Data

**Context**: The Create App dialog needs a pipeline selector. Where do presets come from?

**Findings**:
- `AppCreate` already has optional `pipeline_id?: string` field
- Pipeline configs exist in `pipeline_configs` table (referenced by `apps.associated_pipeline_id` FK)
- The current Solune project has pipeline presets — the new repo won't have any yet
- Backend likely has an endpoint or can expose pipeline configs via existing project settings

**Decision**: Query pipeline configs from the current Solune project via the existing backend API. The frontend will call an endpoint to list available pipeline configurations and populate the dropdown. Default to "None" (no pipeline selected).

**Rationale**: Pipeline presets logically belong to the Solune orchestrator, not the new repository. Using existing pipeline_configs data avoids creating new infrastructure.

**Alternatives Considered**:
1. *Seed presets into the new repo automatically* — Rejected: complex, the new repo shouldn't need its own pipeline configs
2. *Hardcode preset list in frontend* — Rejected: brittle, not data-driven

---

### R6: Parent Issue Close on App Deletion

**Context**: Spec requires closing (not deleting) the parent issue when an app is deleted.

**Findings**:
- Current `delete_app()` only deletes the DB row — no GitHub interaction
- The `delete_app` API endpoint in `api/apps.py` currently passes `db` and `name` only
- A stored memory confirms: `delete_app()` accepts optional `access_token` and `github_service` kwargs to close the parent issue on deletion (best-effort)
- This indicates the feature may already be partially implemented on the branch

**Decision**: Add optional `access_token` and `github_service` kwargs to `delete_app()`. If the app has `parent_issue_number`, call GitHub REST API to close the issue (PATCH `/repos/{owner}/{repo}/issues/{number}` with `state: "closed"`). Best-effort — failure logged, not raised.

**Rationale**: Follows the same best-effort pattern used for all GitHub interactions in app lifecycle. Closing preserves audit trail per spec requirement.

**Alternatives Considered**:
1. *Delete the issue* — Rejected: spec explicitly requires close, not delete; preserves audit trail
2. *Defer to follow-up* — Rejected: included in scope per spec edge cases and FR-013

---

### R7: `.specify/memory/` Directory Exclusion

**Context**: Verify if `.specify/memory/` is intentionally excluded from template copying.

**Findings**:
- `build_template_files()` copies `.specify/` recursively via `rglob("*")`
- The spec assumption states: "The `.specify/memory/` directory is intentionally excluded from template copying"
- Current code has no explicit exclusion — it copies everything under `.specify/`
- The `_is_safe_path()` function blocks symlinks and path traversal but doesn't filter specific subdirectories

**Decision**: The `.specify/memory/` directory contains project-specific memories (constitution, etc.) that should be seeded into new repositories. Per spec assumption, it is intentionally excluded. However, reviewing the actual code shows it IS currently copied. This needs clarification in implementation — the spec assumption may be wrong, or an explicit exclusion needs to be added. Mark as implementation detail for tasks phase.

**Rationale**: The spec lists this as an assumption. Implementation should verify whether memory files should be excluded or included and handle accordingly.

---

## Summary of Decisions

| # | Topic | Decision | Risk |
|---|-------|----------|------|
| R1 | Template error handling | Return `(files, warnings)` tuple | Low — minor signature change |
| R2 | Branch poll backoff | 10 retries, exponential backoff, ~15s max | Low — standard pattern |
| R3 | Parent issue wiring | Private function reusing existing primitives | Medium — multiple async operations |
| R4 | Migration strategy | Simple ALTER TABLE ADD COLUMN | Low — nullable columns, no constraints |
| R5 | Pipeline presets | Query from current Solune project | Low — uses existing data |
| R6 | Close on delete | Optional kwargs, best-effort PATCH | Low — non-blocking |
| R7 | .specify/memory/ | Verify at implementation time | Low — cosmetic |
