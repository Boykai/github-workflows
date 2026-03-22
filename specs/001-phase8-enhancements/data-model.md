# Data Model: Phase 8 Feature Enhancements

**Feature**: `001-phase8-enhancements` | **Date**: 2026-03-22  
**Source**: [spec.md](./spec.md) Key Entities + [research.md](./research.md) design decisions

## Entity Definitions

### 1. PollingSession

Represents the adaptive polling state for a board view, tracking activity levels and interval adjustments.

**Location**: Frontend — React hook state (`useAdaptivePolling`)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `currentInterval` | `number` | Current polling interval in milliseconds | Min: 3000, Max: 60000 |
| `activityScore` | `number` | Rolling activity score (0.0–1.0) | Clamped to [0, 1] |
| `changesWindow` | `boolean[]` | Sliding window of change detection results (last N polls) | Fixed-length array (default: 5) |
| `lastPollTimestamp` | `number` | Unix timestamp of last successful poll | Must be > 0 |
| `backoffMultiplier` | `number` | Exponential backoff multiplier on failures | Min: 1, Max: 32 |
| `consecutiveFailures` | `number` | Count of consecutive poll failures | Min: 0 |
| `isTabVisible` | `boolean` | Whether the browser tab is currently visible | — |
| `tier` | `'high' \| 'medium' \| 'low' \| 'backoff'` | Current polling tier | Enum |

**Interval Tier Mapping**:
| Tier | Activity Score | Interval |
|------|---------------|----------|
| `high` | > 0.6 | 3,000 ms |
| `medium` | 0.2 – 0.6 | 10,000 ms |
| `low` | < 0.2 | 30,000 ms |
| `backoff` | N/A (on error) | base × 2^failures (max 60,000 ms) |

**State Transitions**:
- `idle` → `high`: First change detected in window
- `high` → `medium`: Activity score drops below 0.6
- `medium` → `low`: Activity score drops below 0.2
- `any` → `backoff`: Poll request fails
- `backoff` → `medium`: Poll request succeeds after failure
- `any` → `medium`: Tab regains focus (immediate poll triggered)

---

### 2. PipelineExecution

Represents an individual pipeline run with concurrency and fault isolation metadata.

**Location**: Backend — Extension of existing `PipelineState` in `workflow_orchestrator/models.py`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `pipeline_id` | `str` | Unique identifier for this pipeline execution | Non-empty UUID |
| `pipeline_config_id` | `str` | Reference to the pipeline configuration | Must reference valid config |
| `project_id` | `str` | Owning project identifier | Non-empty |
| `execution_mode` | `str` | `"sequential"` or `"concurrent"` | Enum |
| `status` | `str` | `"pending"`, `"running"`, `"completed"`, `"failed"`, `"cancelled"` | Enum |
| `started_at` | `datetime \| None` | Execution start timestamp | None if pending |
| `completed_at` | `datetime \| None` | Execution completion timestamp | None if not completed |
| `error_message` | `str \| None` | Error details if failed | None if not failed |
| `is_isolated` | `bool` | Whether this execution is fault-isolated from siblings | Default: True |
| `concurrent_group_id` | `str \| None` | Group ID linking concurrent sibling executions | None if sequential |

**Relationships**:
- Many-to-one with Project (via `project_id`)
- Many-to-one with PipelineConfig (via `pipeline_config_id`)
- Self-referencing group via `concurrent_group_id`

**State Transitions**:
- `pending` → `running`: Execution starts (concurrent dispatch or sequential turn)
- `running` → `completed`: All pipeline steps finish successfully
- `running` → `failed`: An unrecoverable error occurs (siblings continue)
- `pending` → `cancelled`: Queue-mode supersedes or project is reconfigured
- `running` → `cancelled`: Manual cancellation

---

### 3. BoardProjection

Represents the lazily loaded subset of board data currently rendered in the client.

**Location**: Frontend — React hook state (`useBoardProjection`)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `loadedItemIds` | `Set<string>` | IDs of items whose DOM nodes are currently mounted | — |
| `visibleRange` | `{ start: number; end: number }` | Index range of currently visible items per column | start ≤ end |
| `bufferSize` | `number` | Number of extra items to render above/below viewport | Default: 10 |
| `totalItemCount` | `number` | Total items in the full dataset (from TanStack Query cache) | ≥ 0 |
| `isInitialRender` | `boolean` | True during first mount, false after | — |
| `pendingColumns` | `Set<string>` | Column IDs with items not yet rendered | — |

**Relationships**:
- One-to-one with Board view instance
- References items in TanStack Query cache (BoardDataResponse)

---

### 4. PipelineConfigFilter

Represents the user's currently selected pipeline filter in the board toolbar.

**Location**: Frontend — Part of `BoardFilterState` in `useBoardControls.ts`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `selectedPipelineConfigId` | `string \| null` | ID of the selected pipeline config, null = "All Pipelines" | Must be valid config ID or null |
| `availablePipelineConfigs` | `PipelineConfigOption[]` | List of available pipeline configs for the dropdown | Derived from board data |

**PipelineConfigOption**:
| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Pipeline config unique identifier |
| `name` | `string` | Human-readable pipeline config name |
| `itemCount` | `number` | Count of items associated with this config |

**Relationships**:
- Part of `BoardFilterState` (composition)
- References `PipelineConfig` entities from board data

---

### 5. RecoveryState

Represents the outcome of label-driven state recovery for a board item.

**Location**: Backend — `recovery.py` / `pipeline_state_store.py`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `issue_number` | `int` | Issue/item number being recovered | > 0 |
| `project_id` | `str` | Project the item belongs to | Non-empty |
| `source_labels` | `list[ParsedLabel]` | Labels found on the item | — |
| `reconstructed_stage` | `str \| None` | Pipeline stage reconstructed from labels | None if ambiguous |
| `reconstructed_status` | `str \| None` | Pipeline status reconstructed from labels | None if ambiguous |
| `confidence` | `str` | `"high"`, `"medium"`, `"low"`, `"ambiguous"` | Enum |
| `ambiguity_flags` | `list[str]` | Descriptions of detected ambiguities | — |
| `requires_manual_review` | `bool` | True if recovery couldn't determine state | Default: False |
| `recovered_at` | `datetime` | Timestamp of recovery | Auto-set |
| `recovery_source` | `str` | `"labels"`, `"database"`, `"mixed"` | Enum |

**State Transitions**:
- `unrecovered` → `recovered (high confidence)`: Labels cleanly map to a single pipeline stage
- `unrecovered` → `recovered (low confidence)`: Labels partially map, some guessing required
- `unrecovered` → `requires_manual_review`: Labels conflict or are missing
- `requires_manual_review` → `recovered`: Admin manually confirms state

---

### 6. CollisionEvent

Represents a detected collision between concurrent operations targeting the same entity.

**Location**: Backend — New model in `models/mcp.py` or dedicated `models/collision.py`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `collision_id` | `str` | Unique collision event identifier | UUID |
| `target_entity_type` | `str` | Type of entity targeted (e.g., `"board_item"`, `"mcp_config"`) | Non-empty |
| `target_entity_id` | `str` | ID of the targeted entity | Non-empty |
| `operation_a` | `CollisionOperation` | First conflicting operation | Required |
| `operation_b` | `CollisionOperation` | Second conflicting operation | Required |
| `resolution_strategy` | `str` | `"last_write_wins"`, `"user_priority"`, `"manual_review"` | Enum |
| `resolution_outcome` | `str` | Description of the resolution result | Non-empty |
| `winning_operation` | `str` | `"a"`, `"b"`, `"neither"` | Enum |
| `detected_at` | `datetime` | Timestamp of collision detection | Auto-set |
| `resolved_at` | `datetime \| None` | Timestamp of resolution | None if pending manual review |

**CollisionOperation**:
| Field | Type | Description |
|-------|------|-------------|
| `operation_id` | `str` | Unique operation identifier |
| `operation_type` | `str` | Type of operation (e.g., `"update"`, `"delete"`, `"move"`) |
| `initiated_by` | `str` | `"user"` or `"automation"` |
| `user_id` | `str \| None` | User who initiated (None if automation) |
| `timestamp` | `datetime` | When the operation was initiated |
| `payload` | `dict` | Operation-specific data |
| `version_expected` | `int` | Version the operation expected to act on |

**Relationships**:
- References target entity (polymorphic via `target_entity_type` + `target_entity_id`)
- Contains two `CollisionOperation` instances

---

### 7. ActionHistoryEntry

Represents a single entry in the undo/redo stack for destructive actions.

**Location**: Frontend — React context (`UndoRedoContext`)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | `string` | Unique entry identifier | UUID |
| `actionType` | `string` | Type of destructive action: `"archive"`, `"delete"`, `"label_remove"`, `"status_change"` | Enum |
| `entityType` | `string` | Type of affected entity: `"board_item"`, `"label"`, `"card"` | Enum |
| `entityId` | `string` | ID of the affected entity | Non-empty |
| `previousState` | `Record<string, unknown>` | Snapshot of entity state before the action | Non-empty |
| `newState` | `Record<string, unknown>` | Snapshot of entity state after the action | Non-empty |
| `timestamp` | `number` | Unix timestamp when the action was performed | > 0 |
| `expiresAt` | `number` | Unix timestamp when the undo window closes | timestamp + windowMs |
| `description` | `string` | Human-readable description (e.g., "Archived issue #42") | Non-empty |
| `isExpired` | `boolean` | Computed: `Date.now() > expiresAt` | Derived |

**Relationships**:
- Part of `UndoRedoContext` state (undo stack or redo stack)
- References board entities by `entityType` + `entityId`

**Stack Behavior**:
- **Undo**: Pop from `undoStack`, restore `previousState`, push to `redoStack`
- **Redo**: Pop from `redoStack`, apply `newState`, push to `undoStack`
- **New action**: Push to `undoStack`, clear `redoStack`
- **Expiry**: Remove entries where `Date.now() > expiresAt`

---

## Entity Relationship Diagram

```text
┌─────────────────┐     ┌─────────────────────┐
│  PollingSession  │     │   BoardProjection   │
│  (Frontend)      │────▶│   (Frontend)        │
│                  │poll │                     │
│  activityScore   │     │  loadedItemIds      │
│  currentInterval │     │  visibleRange       │
└─────────────────┘     └─────────┬───────────┘
                                  │renders
                                  ▼
┌─────────────────┐     ┌─────────────────────┐
│ PipelineConfig   │     │   Board Items       │
│ Filter           │────▶│   (TanStack Cache)  │
│ (Frontend)       │filtr│                     │
│                  │     │  issue data, labels  │
│ selectedConfigId │     │  pipeline config ref │
└─────────────────┘     └─────────┬───────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│ PipelineExec    │ │ RecoveryState │ │ ActionHistory   │
│ (Backend)       │ │ (Backend)     │ │ (Frontend)      │
│                 │ │               │ │                 │
│ status, mode    │ │ source_labels │ │ undoStack       │
│ concurrent_grp  │ │ confidence    │ │ redoStack       │
└───────┬─────────┘ └───────────────┘ └─────────────────┘
        │
        │ concurrent ops
        ▼
┌─────────────────┐
│ CollisionEvent  │
│ (Backend)       │
│                 │
│ operation_a/b   │
│ resolution      │
└─────────────────┘
```

## Database Schema Extensions

### Table: `collision_events` (new)

```sql
CREATE TABLE IF NOT EXISTS collision_events (
    collision_id TEXT PRIMARY KEY,
    target_entity_type TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    operation_a_json TEXT NOT NULL,
    operation_b_json TEXT NOT NULL,
    resolution_strategy TEXT NOT NULL,
    resolution_outcome TEXT NOT NULL,
    winning_operation TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    resolved_at TEXT
);
```

### Table: `recovery_log` (new)

```sql
CREATE TABLE IF NOT EXISTS recovery_log (
    issue_number INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    source_labels_json TEXT NOT NULL,
    reconstructed_stage TEXT,
    reconstructed_status TEXT,
    confidence TEXT NOT NULL,
    ambiguity_flags_json TEXT NOT NULL DEFAULT '[]',
    requires_manual_review INTEGER NOT NULL DEFAULT 0,
    recovered_at TEXT NOT NULL,
    recovery_source TEXT NOT NULL DEFAULT 'labels',
    PRIMARY KEY (issue_number, project_id, recovered_at)
);
```

### Table: `pipeline_states` (extend existing)

Add columns to support concurrent execution tracking:

```sql
ALTER TABLE pipeline_states ADD COLUMN concurrent_group_id TEXT;
ALTER TABLE pipeline_states ADD COLUMN is_isolated INTEGER NOT NULL DEFAULT 1;
ALTER TABLE pipeline_states ADD COLUMN recovered_at TEXT;
```

### Table: `mcp_configurations` (extend existing)

Add version column for optimistic concurrency control:

```sql
ALTER TABLE mcp_configurations ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
```
