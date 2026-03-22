# Data Model: Auto Merge — Automatically Squash-Merge Parent PRs When Pipelines Complete

**Feature**: `001-auto-merge-pipelines` | **Date**: 2026-03-22 | **Plan**: [plan.md](./plan.md)

## Entities

### 1. ProjectBoardConfig (Modified)

**Location**: Backend `solune/backend/src/models/settings.py`, Frontend `solune/frontend/src/types/index.ts`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `column_order` | `list[str]` / `string[]` | `[]` | Visual column ordering |
| `collapsed_columns` | `list[str]` / `string[]` | `[]` | Collapsed column state |
| `show_estimates` | `bool` / `boolean` | `False` | Show estimate column |
| `queue_mode` | `bool` / `boolean` | `False` | *Existing* — Agent queue mode |
| **`auto_merge`** | **`bool`** / **`boolean`** | **`False`** | **NEW** — Auto merge toggle |

**Validation Rules**:
- `auto_merge` is a simple boolean; no cross-field validation required.
- When serialized to SQLite, stored as `INTEGER` (0/1) in a dedicated column (not in JSON blob).

**Storage Path**: `project_settings.auto_merge` column (dedicated, like `queue_mode`).

---

### 2. PipelineState (Modified)

**Location**: Backend `solune/backend/src/services/workflow_orchestrator/models.py`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| *... existing fields ...* | | | |
| **`auto_merge`** | **`bool`** | **`False`** | **NEW** — Resolved auto_merge flag for this pipeline run |

**Validation Rules**:
- Resolved at pipeline start: `auto_merge = project_auto_merge OR pipeline_auto_merge`.
- Immutable once set at pipeline start? No — retroactive toggle can activate it via lazy check at merge decision point.
- Effective value at merge decision: `pipeline_state.auto_merge OR is_auto_merge_enabled(project_id)`.

**Storage Path**: Serialized in `pipeline_state_store.py` metadata JSON (`metadata.auto_merge`).

---

### 3. PipelineConfig (Modified)

**Location**: Backend `solune/backend/src/services/copilot_polling/pipeline.py` (or dedicated config model), Frontend `solune/frontend/src/types/index.ts`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| *... existing fields ...* | | | |
| **`auto_merge`** | **`bool`** / **`boolean`** | **`False`** | **NEW** — Pipeline-level auto merge override |

**Validation Rules**:
- Independent of project-level setting.
- OR logic: if either project OR pipeline `auto_merge` is true, auto merge is active.
- Pipeline-level cannot override a project-level `true` to `false` (by design — OR logic).

**Storage Path**: Pipeline configuration CRUD endpoints (existing persistence layer).

---

### 4. AutoMergeResult (New)

**Location**: Backend `solune/backend/src/services/copilot_polling/auto_merge.py`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `Literal["merged", "devops_needed", "merge_failed"]` | — | Outcome of merge attempt |
| `pr_number` | `int \| None` | `None` | PR number that was targeted |
| `merge_commit` | `str \| None` | `None` | Merge commit SHA on success |
| `error` | `str \| None` | `None` | Error message on failure |
| `context` | `dict \| None` | `None` | CI failure details for DevOps dispatch |

**Validation Rules**:
- `status` is always required.
- `merge_commit` is only set when `status == "merged"`.
- `error` is only set when `status == "merge_failed"`.
- `context` is only set when `status == "devops_needed"`.

---

### 5. CheckRunEvent (New)

**Location**: Backend `solune/backend/src/api/webhook_models.py`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `action` | `str` | — | Event action (`completed`, `created`, etc.) |
| `check_run` | `CheckRunData` | — | Check run details |
| `repository` | `RepositoryData` | — | Repository context (existing model) |

**CheckRunData**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | — | Check run ID |
| `name` | `str` | — | Check run name |
| `status` | `str` | — | `queued`, `in_progress`, `completed` |
| `conclusion` | `str \| None` | `None` | `success`, `failure`, `timed_out`, etc. |
| `head_sha` | `str` | — | Commit SHA |
| `pull_requests` | `list[CheckRunPR]` | `[]` | Associated pull requests |

**CheckRunPR**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `number` | `int` | — | PR number |
| `head` | `BranchRef` | — | Head branch info |
| `base` | `BranchRef` | — | Base branch info |

---

### 6. CheckSuiteEvent (New)

**Location**: Backend `solune/backend/src/api/webhook_models.py`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `action` | `str` | — | Event action (`completed`) |
| `check_suite` | `CheckSuiteData` | — | Check suite details |
| `repository` | `RepositoryData` | — | Repository context (existing model) |

**CheckSuiteData**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | — | Check suite ID |
| `status` | `str` | — | `completed` |
| `conclusion` | `str \| None` | `None` | `success`, `failure`, etc. |
| `head_sha` | `str` | — | Commit SHA |
| `pull_requests` | `list[CheckRunPR]` | `[]` | Associated pull requests |

---

### 7. DevOps Agent Definition (New)

**Location**: `.github/agents/devops.agent.md`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` (YAML frontmatter) | `"DevOps"` |
| `description` | `str` (YAML frontmatter) | Agent capability summary |
| `icon` | `str` (YAML frontmatter) | Lucide icon name (e.g., `"wrench"`) |
| *body* | Markdown | System prompt for CI failure diagnosis |

**Discovery**: Automatically discovered by `list_available_agents()` via `.github/agents/*.agent.md` glob. Slug: `devops`.

---

### 8. DevOps Attempt Tracker (Metadata Extension)

**Location**: `PipelineState.metadata` dict

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `devops_attempts` | `int` | `0` | Number of DevOps agent dispatch attempts |
| `devops_active` | `bool` | `False` | Whether DevOps agent is currently active |

**Validation Rules**:
- `devops_attempts` incremented on each dispatch, capped at 2.
- `devops_active` set to `True` on dispatch, `False` on completion detection.
- After 2nd failed attempt: pipeline marked ERROR, user notified.

---

## Entity Relationships

```text
┌─────────────────────┐
│ ProjectBoardConfig  │
│ ─────────────────── │
│ auto_merge: bool    │──┐
│ queue_mode: bool    │  │ OR logic
└─────────────────────┘  │
                         ▼
┌─────────────────────┐  ┌──────────────────────┐
│   PipelineConfig    │  │  Resolved auto_merge  │
│ ─────────────────── │──┤  at merge decision    │
│ auto_merge: bool    │  │  point                │
└─────────────────────┘  └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    PipelineState      │
                         │ ────────────────────  │
                         │ auto_merge: bool      │
                         │ metadata:             │
                         │   devops_attempts: int│
                         │   devops_active: bool │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │ Human Skip   │ │ Auto Merge   │ │ DevOps       │
           │ (SKIPPED)    │ │ Attempt      │ │ Dispatch     │
           └──────────────┘ └──────┬───────┘ └──────┬───────┘
                                   │                │
                            ┌──────┴───────┐ ┌──────┴───────┐
                            │ merged       │ │ devops_needed│
                            │ merge_failed │ │ (CI failure) │
                            └──────────────┘ └──────────────┘
```

## State Transitions

### Auto Merge Pipeline Lifecycle

```text
Pipeline Start
  │
  ├─ Resolve auto_merge flag (project OR pipeline)
  ├─ Apply "auto-merge" label to issue (FR-004)
  │
  ▼
Agent Steps Execute (normal flow)
  │
  ├─ Last step is "human" AND auto_merge == true?
  │   ├─ YES → Mark SKIPPED (⏭), close sub-issue, skip assignment
  │   └─ NO  → Normal human agent assignment
  │
  ▼
Pipeline Complete (all agents done)
  │
  ├─ Check: pipeline_state.auto_merge OR is_auto_merge_enabled(project_id)
  │   ├─ NO  → Normal transition (status move, dequeue)
  │   └─ YES → _attempt_auto_merge()
  │
  ▼
_attempt_auto_merge()
  │
  ├─ Discover main PR
  ├─ Draft → Ready-for-review
  ├─ Check CI status (get_check_runs_for_ref)
  ├─ Check mergeability (get_pr_mergeable_state)
  │
  ├─ All checks pass + MERGEABLE
  │   └─ merge_pull_request(SQUASH) → "merged"
  │       └─ Broadcast auto_merge_completed
  │
  ├─ CI failure OR CONFLICTING
  │   └─ Return "devops_needed"
  │       ├─ devops_attempts < 2?
  │       │   ├─ YES → dispatch DevOps agent, increment counter
  │       │   │        Broadcast devops_triggered
  │       │   └─ NO  → Mark pipeline ERROR, notify user
  │       │            Broadcast auto_merge_failed
  │       └─ DevOps completes ("devops: Done!" marker)
  │           └─ Retry _attempt_auto_merge()
  │
  └─ Merge API fails
      └─ Return "merge_failed"
          └─ Mark pipeline ERROR, notify user
              Broadcast auto_merge_failed
```

## Database Schema Changes

### Migration: `034_auto_merge.sql`

```sql
-- Add auto_merge column to project_settings for per-project auto merge toggle.
-- When auto_merge = 1, pipelines automatically squash-merge parent PRs on completion.
ALTER TABLE project_settings ADD COLUMN auto_merge INTEGER NOT NULL DEFAULT 0;
```

### Affected Tables

| Table | Column | Type | Default | Purpose |
|-------|--------|------|---------|---------|
| `project_settings` | `auto_merge` | `INTEGER NOT NULL` | `0` | Project-level toggle |
| `pipeline_states` | `metadata` (JSON) | `TEXT` | `'{}'` | Contains `auto_merge`, `devops_attempts`, `devops_active` |

### No New Tables Required

All new data fits into existing table structures via column addition (project_settings) or metadata JSON extension (pipeline_states).
