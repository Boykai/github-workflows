# Research: Debug & Fix Apps Page — New App Creation UX

**Feature**: `051-fix-app-creation-ux` | **Date**: 2026-03-17

## Research Tasks

### R-001: Template File Error Handling Best Practices

**Context**: `build_template_files()` in `template_files.py` silently skips files that fail to read via a bare `continue` in the exception handler. Need to determine the best pattern for collecting and propagating warnings.

**Decision**: Collect errors into a `warnings: list[str]` alongside the file list, returning a `tuple[list[dict], list[str]]` from `build_template_files()`. Each warning includes the file path and the exception message (e.g., `"Failed to read template file '.github/agents/copilot.md': UnicodeDecodeError: ..."`).

**Rationale**: The tuple return is the simplest change — it preserves the existing call pattern while adding warning information. The caller (`create_app_with_new_repo()`) already has a warnings collection mechanism for Azure secrets, so extending it to template files is natural. Raising exceptions would break the best-effort contract; returning a separate object (dataclass) is over-engineering for two fields.

**Alternatives considered**:
- **Raise on any failure**: Rejected — violates the best-effort design decision. One bad file shouldn't block the entire app creation.
- **Return a NamedTuple/dataclass**: Rejected — adds a new type for a simple pair; overkill for this use case.
- **Log-only (current behavior)**: Rejected — users have no visibility into which files failed.

---

### R-002: `.specify/memory/` Directory Inclusion in Templates

**Context**: The spec asks to verify whether `.specify/memory/` is intentionally excluded from template files.

**Decision**: `.specify/memory/` SHOULD be intentionally excluded from template files. The `build_template_files()` function copies the `.specify/` directory tree, but the `memory/` subdirectory contains repository-specific content (constitution, learned facts) that should not be templated into new apps. New apps should start with a clean `.specify/memory/` directory, or the directory can be seeded with a default constitution during pipeline setup.

**Rationale**: The `constitution.md` and any future memory files are specific to the Solune monorepo. Copying them verbatim into a new app repo would create confusion. The template file logic already handles directory traversal — if `.specify/memory/` contents are absent from the source template directory, they're naturally excluded.

**Alternatives considered**:
- **Include all `.specify/` content**: Rejected — would copy Solune-specific constitution into new app repos.
- **Include with placeholder content**: Deferred — could be a follow-up to seed a starter constitution, but not part of this fix.

---

### R-003: Exponential Backoff Pattern for Branch-Readiness Polling

**Context**: Current implementation uses 5 retries × 1s fixed delay = 5s max. Spec requires ~10 retries with exponential backoff for ~15s max.

**Decision**: Use standard exponential backoff: `delay = min(base * 2^attempt, max_delay)` where `base=0.5s`, `max_delay=4s`, for 10 attempts. Total worst-case: 0.5 + 1 + 2 + 4 + 4 + 4 + 4 + 4 + 4 + 4 = ~27.5s. To hit ~15s target: use `base=0.3s`, `max_delay=3s`, 10 attempts → 0.3 + 0.6 + 1.2 + 2.4 + 3 + 3 + 3 + 3 + 3 + 3 = ~22.5s. More practically: 8 attempts with `base=0.5s`, `max_delay=3s` → 0.5 + 1 + 2 + 3 + 3 + 3 + 3 + 3 = ~18.5s. This provides reasonable coverage for GitHub API latency spikes.

**Rationale**: Exponential backoff is the industry standard for retrying API calls. It reduces load on GitHub during spikes while still succeeding quickly when the branch is available fast. The cap at 3s prevents excessive individual waits.

**Alternatives considered**:
- **Fixed 1s interval, more retries**: Rejected — hammers the API unnecessarily during delays.
- **Linear backoff**: Rejected — less effective at reducing early load; exponential is standard.
- **No backoff, just increase retry count**: Rejected — doesn't reduce API pressure.

---

### R-004: Parent Issue Creation Pattern from `_create_parent_issue_sub_issues()`

**Context**: The existing pattern in `tasks.py` creates sub-issues after a parent issue is added to a project. Need to adapt this for the app creation flow.

**Decision**: Extract the reusable pattern from `_create_parent_issue_sub_issues()` and adapt it for `create_app_with_new_repo()`:
1. After template file commit succeeds, check if `pipeline_id` is provided
2. Load `WorkflowConfiguration` using the pipeline_id
3. Create parent issue via `github_projects_service.create_issue()` with body from `append_tracking_to_body()`
4. Add issue to project, set Backlog status
5. Call `orchestrator.create_all_sub_issues()` with the `WorkflowContext`
6. Initialize `PipelineState` and call `ensure_polling_started()`
7. Store `parent_issue_number` and `parent_issue_url` on the App record
8. All steps are best-effort: failures add warnings, don't block app creation

**Rationale**: This follows the exact same pattern already proven in `tasks.py` and `orchestrator.py`. The key difference is the error handling: in the task API, exceptions are silently caught; in app creation, we surface them as warnings.

**Alternatives considered**:
- **Defer pipeline start to a separate API call**: Rejected — adds UX friction; user would need to manually trigger pipeline after creation.
- **Create a new orchestration method**: Rejected — the existing building blocks are sufficient; a new method would duplicate logic.
- **Background job for pipeline setup**: Considered but rejected for MVP — adds complexity with job management; best-effort inline is simpler. Could be a follow-up for very large pipelines.

---

### R-005: Pipeline Presets Source for Frontend Dropdown

**Context**: The spec asks whether pipeline presets should come from the current Solune project or be seeded into the new repo.

**Decision**: Query pipeline presets from the current Solune project using the existing `pipelinesApi.getAssignment(projectId)` and pipeline list query (`['pipelines', projectId]`). The new repo won't have presets yet, so the dropdown shows presets from the Solune project that is currently active.

**Rationale**: The frontend already has hooks for fetching pipeline data (`usePipelineConfig`). The project ID is available in the current context. This is the simplest approach that provides immediate value.

**Alternatives considered**:
- **Seed presets into new repo's project**: Rejected for MVP — requires creating a GitHub Project V2 in the new repo AND copying preset configs; overly complex for the initial implementation.
- **Hardcode preset list**: Rejected — not maintainable and doesn't reflect actual configurations.

---

### R-006: Parent Issue Body Content

**Context**: The spec asks what content to include in the Parent Issue body.

**Decision**: Include the app description, a link back to the Solune dashboard (if available), and the tracking table generated by `append_tracking_to_body()`. This matches the existing `recommendations/confirm` pattern.

**Rationale**: The tracking table is essential for agent pipeline visibility. The app description provides context for anyone viewing the issue. The dashboard link creates a bidirectional connection between the Solune UI and GitHub.

**Alternatives considered**:
- **Minimal body (tracking table only)**: Rejected — loses context about what the app is for.
- **Full spec dump**: Rejected — too much content; the tracking table is the actionable part.

---

### R-007: App Deletion — Close vs Delete Parent Issue

**Context**: The spec mentions closing (not deleting) the parent issue when an app is deleted.

**Decision**: Include parent issue closure in this feature scope. On `DELETE /apps/{name}`, if the app has a `parent_issue_number`, call the GitHub API to close the issue. This is a best-effort operation — failure logs a warning but doesn't block deletion.

**Rationale**: Leaving orphaned open issues creates noise in the repository. Closing (not deleting) preserves the audit trail. The implementation is minimal: one additional API call in the delete handler.

**Alternatives considered**:
- **Defer to follow-up**: Rejected — it's a small addition and prevents orphaned issues from day one.
- **Delete the issue**: Rejected — deleting GitHub issues removes audit trail and is irreversible.

---

### R-008: Database Migration Strategy for New App Fields

**Context**: Need to add `parent_issue_number` (integer, nullable) and `parent_issue_url` (text, nullable) to the `apps` table.

**Decision**: Create migration `029_app_parent_issue.sql` using `ALTER TABLE apps ADD COLUMN` statements. Both columns are nullable with no default, so existing rows are unaffected. No table recreation needed (unlike migration 028 which changed a CHECK constraint).

**Rationale**: Simple `ALTER TABLE ADD COLUMN` is the safest migration approach for nullable columns. It doesn't require data migration or table recreation. The existing migration pattern (sequential numbering, raw SQL) is followed exactly.

**Alternatives considered**:
- **Table recreation with INSERT...SELECT**: Rejected — unnecessary when only adding nullable columns; ADD COLUMN is sufficient for SQLite.
- **Combined with other schema changes**: Rejected — single-purpose migrations are easier to understand and roll back.

---

### R-009: Frontend Warning Toast Styling

**Context**: Currently `showError(createdApp.warnings[0])` displays only the first warning using error styling. Need to show all warnings with warning-style toasts.

**Decision**: Replace the single `showError` call with iteration over all warnings, using a `showWarning` toast variant (or `showSuccess` with a ⚠ prefix if no dedicated warning style exists). Display a structured summary toast: ✓ Repository created / ✓ Template files committed / ✓ Pipeline started / ⚠ {warning1} / ⚠ {warning2}.

**Rationale**: Users need complete visibility into what happened. Warning-style (yellow/amber) toasts visually distinguish non-fatal issues from hard errors (red). The structured summary matches the acceptance scenarios in the spec.

**Alternatives considered**:
- **Single consolidated warning message**: Considered — could join all warnings into one toast. Rejected because individual toasts are easier to read and dismiss independently.
- **Warning panel instead of toasts**: Rejected for MVP — toasts match the existing UX pattern; a panel would be a larger design change.

## Summary of Resolved Clarifications

| ID | Unknown | Resolution |
|----|---------|------------|
| R-001 | Template error propagation method | Return `tuple[list[dict], list[str]]` from `build_template_files()` |
| R-002 | `.specify/memory/` inclusion | Intentionally excluded — repo-specific content |
| R-003 | Backoff algorithm | Exponential backoff, base=0.5s, max=3s, 8 attempts (~18.5s max) |
| R-004 | Parent issue creation pattern | Adapt `_create_parent_issue_sub_issues()` inline in `create_app_with_new_repo()` |
| R-005 | Pipeline presets source | Current Solune project's pipelines |
| R-006 | Parent issue body content | App description + dashboard link + tracking table |
| R-007 | App deletion cleanup | Close parent issue (best-effort) — included in this scope |
| R-008 | Migration strategy | `ALTER TABLE ADD COLUMN` for nullable fields |
| R-009 | Warning toast styling | Iterate all warnings, use warning-style toasts + structured summary |

All NEEDS CLARIFICATION items resolved. Proceeding to Phase 1.
