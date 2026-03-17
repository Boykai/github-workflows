# Data Model: Solune v0.1.0 Public Release

**Branch**: `050-solune-v010-release` | **Date**: 2026-03-17 | **Plan**: [plan.md](./plan.md)

## Overview

This document defines the data entities, relationships, validation rules, and state transitions for the Solune v0.1.0 release. Entities are derived from the feature specification's Key Entities section and functional requirements. The data model extends the existing SQLite schema (migrations 023–028) with new tables for pipeline state persistence and group execution.

---

## Entities

### 1. Pipeline Run

**Description**: A single execution of a pipeline configuration, tracking state for each stage from initiation through completion or failure.

**Source**: Spec Key Entity "Pipeline Run", FR-001 through FR-003, US-1

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique run identifier |
| `pipeline_config_id` | INTEGER | FK → pipeline_configs(id), NOT NULL | Associated pipeline configuration |
| `project_id` | TEXT | NOT NULL | GitHub project node ID |
| `status` | TEXT | NOT NULL, CHECK IN ('pending', 'running', 'completed', 'failed', 'cancelled') | Overall run status |
| `started_at` | TEXT | NOT NULL, ISO 8601 | Run start timestamp |
| `completed_at` | TEXT | NULL, ISO 8601 | Run completion timestamp |
| `trigger` | TEXT | NOT NULL, DEFAULT 'manual' | How the run was initiated (manual, webhook, scheduled) |
| `error_message` | TEXT | NULL | Error details if status is 'failed' |
| `metadata` | TEXT | NULL, JSON | Additional run metadata |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Validation Rules**:
- `completed_at` MUST be NULL when `status` is 'pending' or 'running'
- `completed_at` MUST be set when `status` is 'completed', 'failed', or 'cancelled'
- `error_message` SHOULD only be set when `status` is 'failed'
- No artificial cap on row count (FR-003)

**Indexes**:
- `idx_pipeline_runs_config` ON (pipeline_config_id)
- `idx_pipeline_runs_project` ON (project_id)
- `idx_pipeline_runs_status` ON (status) WHERE status IN ('pending', 'running')

---

### 2. Pipeline Stage State

**Description**: Tracks the execution state of individual stages within a pipeline run, including group membership.

**Source**: Spec Key Entity "Pipeline Run" (stage states), FR-001, FR-015, US-1

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique state identifier |
| `pipeline_run_id` | INTEGER | FK → pipeline_runs(id) ON DELETE CASCADE, NOT NULL | Parent pipeline run |
| `stage_id` | TEXT | NOT NULL | Stage identifier from pipeline config |
| `group_id` | INTEGER | FK → stage_groups(id), NULL | Group this stage belongs to (NULL = ungrouped) |
| `status` | TEXT | NOT NULL, CHECK IN ('pending', 'running', 'completed', 'failed', 'skipped') | Stage execution status |
| `started_at` | TEXT | NULL, ISO 8601 | Stage start timestamp |
| `completed_at` | TEXT | NULL, ISO 8601 | Stage completion timestamp |
| `agent_id` | TEXT | NULL | Agent assigned to this stage |
| `output` | TEXT | NULL, JSON | Stage output/result data |
| `label_name` | TEXT | NULL | GitHub label used for state tracking (FR-015) |
| `error_message` | TEXT | NULL | Error details if status is 'failed' |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Validation Rules**:
- `started_at` MUST be set when `status` transitions from 'pending' to 'running'
- Unique constraint on (pipeline_run_id, stage_id)
- `label_name` follows format: `solune:pipeline:{run_id}:stage:{stage_id}:{status}`

**Indexes**:
- `idx_stage_states_run` ON (pipeline_run_id)
- `idx_stage_states_status` ON (status) WHERE status IN ('pending', 'running')

---

### 3. Stage Group

**Description**: A logical grouping of pipeline stages with a defined execution mode (sequential or parallel).

**Source**: Spec Key Entity "Stage Group", FR-016, FR-017, US-4

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique group identifier |
| `pipeline_config_id` | INTEGER | FK → pipeline_configs(id) ON DELETE CASCADE, NOT NULL | Parent pipeline configuration |
| `name` | TEXT | NOT NULL | Human-readable group name |
| `execution_mode` | TEXT | NOT NULL, CHECK IN ('sequential', 'parallel'), DEFAULT 'sequential' | How stages in this group execute |
| `order_index` | INTEGER | NOT NULL | Execution order relative to other groups |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Validation Rules**:
- `order_index` MUST be unique within a pipeline_config_id
- `name` MUST NOT be empty
- Unique constraint on (pipeline_config_id, order_index)

**Indexes**:
- `idx_stage_groups_config` ON (pipeline_config_id)

---

### 4. Project (Existing — Extended)

**Description**: A workspace representing a GitHub repository with associated pipeline configurations, agents, and access controls. Existing entity extended with access control metadata.

**Source**: Spec Key Entity "Project", FR-006, US-2

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| *Existing fields* | — | — | All current project fields retained |
| `access_control_enabled` | INTEGER | NOT NULL, DEFAULT 1 | Whether project-level access control is active |

**Validation Rules**:
- When `access_control_enabled` = 1, all project resource requests MUST verify user membership
- Unauthorized access returns HTTP 403 (FR-006)

**Note**: The existing project table schema is defined in migration `023_consolidated_schema.sql`. Extension adds a column via new migration.

---

### 5. Agent (Existing — Extended)

**Description**: An AI coding agent instance with assigned role, MCP tool configuration, and visual identity for side-by-side display.

**Source**: Spec Key Entity "Agent", FR-018, FR-019, US-5

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| *Existing fields* | — | — | All current agent fields retained |
| `visual_identifier` | TEXT | NULL | Color/icon identifier for side-by-side display |
| `display_order` | INTEGER | NULL | Order in parallel layout |

**Validation Rules**:
- `visual_identifier` SHOULD be unique within a pipeline run's concurrent agents
- MCP tools MUST be propagated on project settings update (FR-019)

---

### 6. MCP Tool Configuration (Existing)

**Description**: The set of Model Context Protocol tools available to agents within a project. Propagated to agent configuration files on update.

**Source**: Spec Key Entity "MCP Tool Configuration", FR-019, US-5

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| *Existing fields* | — | — | Current MCP config fields retained |

**Behavior Rules**:
- On update: System MUST propagate new tool list to all agent configuration files
- Agent files MUST include `tools: ["*"]` or the explicit tool list
- Propagation is synchronous with the settings save operation

---

### 7. User Session (Existing — Hardened)

**Description**: An authenticated user's active session with enhanced security controls.

**Source**: Spec Key Entity "User Session", FR-004, FR-005, US-2

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| *Existing fields* | — | — | Current session fields retained |

**Security Rules (New)**:
- All cookies MUST set `HttpOnly=True` (FR-004)
- All cookies MUST set `SameSite=Strict` (FR-004)
- `Secure` flag auto-enabled for HTTPS connections
- `Max-Age` defaults to 28800 seconds (8 hours) per existing config

---

### 8. Onboarding Tour State (New)

**Description**: Per-user tracking of onboarding progress, supporting pause, resume, and restart.

**Source**: Spec Key Entity "Onboarding Tour State", FR-038, US-8, Edge Case #6

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique state identifier |
| `user_id` | TEXT | NOT NULL, UNIQUE | GitHub user ID |
| `current_step` | INTEGER | NOT NULL, DEFAULT 0 | Current tour step (0 = not started, 1–9 = in progress, 10 = completed) |
| `completed` | INTEGER | NOT NULL, DEFAULT 0 | Whether tour was completed (0/1) |
| `dismissed_at` | TEXT | NULL, ISO 8601 | When user dismissed the tour (edge case #6) |
| `completed_at` | TEXT | NULL, ISO 8601 | When user completed the tour |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Validation Rules**:
- `current_step` range: 0–10 (0 = not started, 1–9 = tour steps, 10 = completed)
- `completed` = 1 implies `current_step` = 10 and `completed_at` is set
- Tour can be restarted from Help page: resets `current_step` to 1, `completed` to 0, clears `dismissed_at`

**State Transitions**:
- `not_started` (step=0) → `in_progress` (step=1..9): User begins or resumes tour
- `in_progress` → `completed` (step=10): User finishes all 9 steps
- `in_progress` → `dismissed`: User dismisses mid-tour (preserves step for resume)
- `completed` → `in_progress` (step=1): User restarts from Help page
- `dismissed` → `in_progress` (step=N): User resumes from where they left off

---

## Relationships

```text
Pipeline Configuration (existing)
├── has many → Stage Groups (new)
│   └── has many → Pipeline Stage States (via group_id)
├── has many → Pipeline Runs (new)
│   └── has many → Pipeline Stage States (new)
└── belongs to → Project (existing)

Project (existing)
├── has many → Pipeline Configurations (existing)
├── has many → Agents (existing)
├── has one → MCP Tool Configuration (existing)
└── has many → User access records (existing)

User (existing)
├── has many → User Sessions (existing, hardened)
└── has one → Onboarding Tour State (new)
```

## State Transitions

### Pipeline Run Lifecycle

```text
[Created] → pending
              │
              ▼
           running ──────► failed
              │               │
              ▼               ▼
          completed       cancelled
```

**Transition Rules**:
- `pending` → `running`: All prerequisite stage groups resolved, execution begins
- `running` → `completed`: All stages in all groups reached 'completed' or 'skipped'
- `running` → `failed`: Any stage in a sequential group fails (parallel group continues other stages)
- `running` → `cancelled`: User manually cancels the run
- `pending` → `cancelled`: User cancels before execution starts
- No backward transitions (failed → running requires a new run)

### Pipeline Stage Lifecycle

```text
[Created] → pending
              │
              ▼
           running ──────► failed
              │
              ▼
          completed
              
[Any non-running] → skipped (when parent run is cancelled)
```

**Transition Rules**:
- `pending` → `running`: Group execution order reached, stage is next to execute
- `running` → `completed`: Stage agent reports success
- `running` → `failed`: Stage agent reports failure or timeout
- `pending` → `skipped`: Parent run cancelled, stage never started
- In parallel groups: All stages transition to 'running' simultaneously
- In sequential groups: Stages transition to 'running' one at a time in order

### Onboarding Tour Lifecycle

```text
[Created] → not_started (step=0)
                │
                ▼
           in_progress (step=1..9)
              │         │
              ▼         ▼
          completed   dismissed
          (step=10)   (step=N, preserved)
              │         │
              └────┬────┘
                   ▼
           in_progress (step=1 or N, restart/resume)
```

---

## Migration Plan

### New Migration: `029_pipeline_state_persistence.sql`

Creates tables for pipeline runs, stage states, stage groups, and onboarding tour state.

**Tables Created**:
1. `pipeline_runs` — Pipeline execution tracking
2. `pipeline_stage_states` — Per-stage execution state
3. `stage_groups` — Stage grouping with execution mode
4. `onboarding_tour_state` — Per-user onboarding progress

**Columns Added to Existing Tables**:
1. `projects` → `access_control_enabled` (INTEGER, DEFAULT 1)
2. `agents` → `visual_identifier` (TEXT, NULL), `display_order` (INTEGER, NULL)

### Migration Sequence

```text
028_new_repo_support.sql  (existing, last migration)
029_pipeline_state_persistence.sql  (new: pipeline runs, stage states, stage groups, onboarding)
```

The migration follows the established pattern: sequential numbering, SQL-based, applied on startup by the database service.
