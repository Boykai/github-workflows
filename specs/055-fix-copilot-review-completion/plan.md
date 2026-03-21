# Implementation Plan: Fix Premature Copilot Review Completion in Agent Pipeline

**Branch**: `055-fix-copilot-review-completion` | **Date**: 2026-03-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/055-fix-copilot-review-completion/spec.md`

## Summary

The pipeline marks `copilot-review` as "Done!" before it is actually `copilot-review`'s turn because of three compounding issues: the webhook unconditionally moves issues to "In Review", the completion-detection function (`_check_copilot_review_done`) has no pipeline-position guard, and the review-request timestamp is lost on server restart. This plan adds layered guards (pipeline-position checks in the completion detector, the `check_in_review_issues` poller, and the webhook handler), persists the review-request timestamp to SQLite for restart durability, and hardens pipeline reconstruction to prevent false `current_agent` assignment.

## Technical Context

**Language/Version**: Python 3.13 (backend)
**Primary Dependencies**: FastAPI (API framework), httpx (HTTP client), githubkit (GitHub API), aiosqlite (async SQLite)
**Storage**: SQLite with aiosqlite (durable state), in-memory `BoundedDict` (fast access)
**Testing**: ruff (linting), pyright (type checking); unit tests optional per constitution
**Target Platform**: Linux server (backend service)
**Project Type**: Web application (backend-only changes for this feature)
**Performance Goals**: Guards must add zero additional API calls when short-circuiting; durable timestamp write adds at most one SQLite INSERT per review request
**Constraints**: Must preserve backward compatibility for non-pipeline-tracked issues; webhook must still move non-pipeline issues to "In Review"
**Scale/Scope**: 4 files modified (helpers.py, pipeline.py, webhooks.py, state.py), 1 new migration file, ~50 lines of guard logic, ~30 lines of SQLite persistence

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` includes 4 prioritized user stories (P1×2, P2×2) with Given-When-Then acceptance criteria, edge cases, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`; tasks deferred to `/speckit.tasks` |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not mandated by spec; existing linting validates no regressions. Tests are optional per constitution |
| V. Simplicity and DRY | ✅ PASS | Guards are simple boolean checks added inline to existing functions. SQLite persistence reuses the existing migrations infrastructure. No new abstractions, no new libraries, no new patterns |

**Gate Result**: ✅ ALL GATES PASS — proceed to Phase 0.

**Post-Phase 1 Re-check**: ✅ ALL GATES STILL PASS — no new complexity introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/055-fix-copilot-review-completion/
├── plan.md              # This file
├── research.md          # Phase 0 — research findings
├── data-model.md        # Phase 1 — entity model
├── quickstart.md        # Phase 1 — implementation quickstart
├── contracts/           # Phase 1 — internal contracts (no external API)
│   └── internal-guards.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/
│   │   └── webhooks.py              # MODIFY: add pipeline-position guard to update_issue_status_for_copilot_pr()
│   ├── migrations/
│   │   └── 033_copilot_review_requests.sql  # ADD: durable timestamp table
│   └── services/
│       └── copilot_polling/
│           ├── helpers.py            # MODIFY: add pipeline param + guard to _check_copilot_review_done(),
│           │                         #         pass pipeline from _check_agent_done_on_sub_or_parent(),
│           │                         #         add SQLite write/read to timestamp functions
│           ├── pipeline.py           # MODIFY: add pipeline-position guard to check_in_review_issues()
│           └── state.py              # REFERENCE: _copilot_review_requested_at, _copilot_review_first_detected
└── tests/                            # Optional test coverage
```

**Structure Decision**: Backend-only changes within the existing `solune/backend/` tree. All changes modify existing files except one new SQL migration file. No frontend changes required.

## Implementation Phases

### Phase 1 — Pipeline Position Guards (P1, blocks Phase 2)

Sequential dependency chain:

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 1.1 | `helpers.py` | Add optional `pipeline` parameter to `_check_copilot_review_done()`. If `pipeline` is provided and `pipeline.current_agent != "copilot-review"`, return `False` immediately with a warning log — before any API calls. | — |
| 1.2 | `helpers.py` | In `_check_agent_done_on_sub_or_parent()` at the `copilot-review` branch (~line 194), pass the existing `pipeline` parameter through to `_check_copilot_review_done()`. | 1.1 |
| 1.3 | `pipeline.py` | In `check_in_review_issues()`, after pipeline retrieval (~line 2328), if `pipeline.current_agent != "copilot-review"` and `pipeline.status` is earlier than "In Review", log a warning and let `_process_pipeline_completion()` handle advancing the current (non-copilot-review) agent only. | — (parallel with 1.1–1.2) |

### Phase 2 — Webhook Guard (P1, depends on Phase 1)

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 2.1 | `webhooks.py` | In `update_issue_status_for_copilot_pr()`, before the `update_item_status_by_name("In Review")` call (~line 557), check pipeline state: if a pipeline exists AND `pipeline.current_agent != "copilot-review"` AND `pipeline.status != "In Review"` → do NOT move the issue, log and return a "skipped" result. If no pipeline exists → still move (backward compat). | Phase 1 |

### Phase 3 — Durable Review-Request Timestamp (P2, parallel with Phase 2)

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 3.1 | `migrations/` | Create `033_copilot_review_requests.sql` with table: `copilot_review_requests(issue_number INTEGER PRIMARY KEY, requested_at TEXT NOT NULL, project_id TEXT)` | — |
| 3.2 | `helpers.py` | In `_record_copilot_review_request_timestamp()`, after storing in `_copilot_review_requested_at` dict, also INSERT/REPLACE into `copilot_review_requests` table via aiosqlite. | 3.1 |
| 3.3 | `helpers.py` | In `_check_copilot_review_done()`, when `_copilot_review_requested_at.get(issue_number)` is `None`, query `copilot_review_requests` table before falling back to issue body HTML comment parsing. | 3.1, 3.2 |

### Phase 4 — Reconstruction Safety (P2, depends on Phase 1)

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 4.1 | `pipeline.py` | Verify the existing tracking-table guard in `_get_or_reconstruct_pipeline()` (lines ~404–451) correctly handles "In Progress agents pending but board says In Review". The existing code already handles this case — the `first_incomplete` check at line 406 detects pending agents in earlier statuses and reconstructs for that status. Confirm with test coverage. | Phase 1 |

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Guard placement | Layered: completion detector → poller → webhook | Defense-in-depth: each layer independently prevents false completion. Even if one guard fails, others catch the error |
| Pipeline parameter passing | Optional `pipeline` kwarg to `_check_copilot_review_done()` | Non-breaking change; callers without pipeline context still work (guard is skipped) |
| Webhook backward compat | Only guard pipeline-tracked issues | Non-pipeline issues (legacy, external) continue to get status moves from webhooks |
| Timestamp storage | SQLite `copilot_review_requests` table | Survives server restarts; consistent with existing migration infrastructure (032_activity_events.sql pattern) |
| Timestamp recovery priority | In-memory → SQLite → HTML comment | Fast path first; durable fallback; HTML comment as last resort (unreliable but preserved) |
| Scope exclusions | No changes to: polling loop order, confirmation delay timing, `_advance_pipeline()` | These are already correct once called with the right agent; fixing the guards upstream is sufficient |

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
