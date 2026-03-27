# Data Model: Self-Evolving Roadmap Engine

**Feature Branch**: `001-roadmap-engine` | **Date**: 2026-03-27
**Phase**: 1 — Design & Contracts

## Entities

### RoadmapConfig (extends ProjectBoardConfig)

Per-project roadmap configuration stored as JSON in the existing `project_settings` table via `ProjectBoardConfig`.

| Field | Type | Default | Validation | Description |
|-------|------|---------|------------|-------------|
| `roadmap_enabled` | `bool` | `False` | — | Master toggle for roadmap engine |
| `roadmap_seed` | `str` | `""` | Max 10,000 chars; non-empty when generating | Product vision text guiding AI generation |
| `roadmap_batch_size` | `int` | `3` | `1 ≤ x ≤ 10` | Number of items per generation cycle |
| `roadmap_pipeline_id` | `str \| None` | `None` | Must reference an existing active pipeline | Target pipeline for launching generated items |
| `roadmap_auto_launch` | `bool` | `False` | — | Enable automatic generation on idle pipeline |
| `roadmap_grace_minutes` | `int` | `0` | `0 ≤ x ≤ 1440` | Minutes to hold items before auto-launching (veto window) |

**Storage**: Added as fields on `ProjectBoardConfig` Pydantic model (`src/models/settings.py`). Persisted as part of the `board_display_config` JSON column in `project_settings`. No schema migration required.

**Pydantic definition** (extends existing class):

```python
class ProjectBoardConfig(BaseModel):
    """Board display configuration for a project."""
    # Existing fields
    column_order: list[str] = Field(default_factory=list)
    collapsed_columns: list[str] = Field(default_factory=list)
    show_estimates: bool = False
    queue_mode: bool = False
    auto_merge: bool = False
    # Roadmap fields (FR-001)
    roadmap_enabled: bool = False
    roadmap_seed: str = ""
    roadmap_batch_size: int = Field(default=3, ge=1, le=10)
    roadmap_pipeline_id: str | None = None
    roadmap_auto_launch: bool = False
    roadmap_grace_minutes: int = Field(default=0, ge=0, le=1440)
```

---

### RoadmapItem

A single AI-generated feature proposal within a batch.

| Field | Type | Validation | Description |
|-------|------|------------|-------------|
| `title` | `str` | Non-empty, max 256 chars | Feature proposal title |
| `body` | `str` | Non-empty | Full issue body text (markdown) |
| `rationale` | `str` | Non-empty | Explanation of why this feature was suggested |
| `priority` | `str` | One of: `P0`, `P1`, `P2`, `P3` | Priority level |
| `size` | `str` | One of: `XS`, `S`, `M`, `L`, `XL` | T-shirt size estimate |

**Pydantic definition**:

```python
class RoadmapItem(BaseModel):
    """A single AI-generated feature proposal (FR-002)."""
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    priority: Literal["P0", "P1", "P2", "P3"]
    size: Literal["XS", "S", "M", "L", "XL"]
```

---

### RoadmapBatch

A collection of RoadmapItems produced by a single generation cycle.

| Field | Type | Validation | Description |
|-------|------|------------|-------------|
| `items` | `list[RoadmapItem]` | Non-empty, length ≤ 10 | Generated feature proposals |
| `project_id` | `str` | Non-empty | Owning project identifier |
| `user_id` | `str` | Non-empty | User who triggered the generation |
| `generated_at` | `datetime` | Auto-set to UTC now | Timestamp of generation |

**Pydantic definition**:

```python
class RoadmapBatch(BaseModel):
    """A batch of AI-generated feature proposals from one cycle (FR-002)."""
    items: list[RoadmapItem] = Field(..., min_length=1, max_length=10)
    project_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

---

### RoadmapCycleLog

Audit record persisted to the `roadmap_cycles` SQLite table.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | Auto-increment | Unique cycle identifier |
| `project_id` | `str` | — | Project this cycle belongs to |
| `user_id` | `str` | — | User who triggered the cycle |
| `batch_json` | `str` | — | Serialized `RoadmapBatch` (JSON string) |
| `status` | `str` | `"pending"` | Cycle status: `pending`, `completed`, `failed` |
| `created_at` | `str` | ISO-8601 UTC now | Cycle creation timestamp |

**Pydantic definition** (for API responses):

```python
class RoadmapCycleStatus(StrEnum):
    """Possible states for a roadmap generation cycle."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class RoadmapCycleLog(BaseModel):
    """Audit record for a roadmap generation cycle (FR-003)."""
    id: int
    project_id: str
    user_id: str
    batch_json: str  # Serialized RoadmapBatch
    status: RoadmapCycleStatus = RoadmapCycleStatus.PENDING
    created_at: str

    @property
    def batch(self) -> RoadmapBatch:
        """Deserialize batch_json into a RoadmapBatch."""
        return RoadmapBatch.model_validate_json(self.batch_json)
```

---

### RoadmapCycleLog — SQLite Schema

**Migration**: `039_roadmap_cycles.sql`

```sql
CREATE TABLE IF NOT EXISTS roadmap_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    batch_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_roadmap_cycles_project_id
    ON roadmap_cycles(project_id);

CREATE INDEX IF NOT EXISTS idx_roadmap_cycles_project_created
    ON roadmap_cycles(project_id, created_at DESC);
```

## Relationships

```text
ProjectBoardConfig (existing)
  └─ contains ── RoadmapConfig fields (embedded, not a separate entity)

RoadmapBatch
  ├─ contains 1..10 ── RoadmapItem
  ├─ belongs to ── project_id (project_settings)
  └─ triggered by ── user_id

RoadmapCycleLog (persisted)
  ├─ stores ── RoadmapBatch (as batch_json)
  ├─ belongs to ── project_id
  └─ triggered by ── user_id

Pipeline Launch Flow:
  RoadmapBatch.items[]
    └─ each item → execute_pipeline_launch(issue_description=item.body)
       └─ creates GitHub issue (existing logic, no new code)
```

## State Transitions

### Cycle Status

```text
[trigger: manual or auto-launch]
        │
        v
    ┌─────────┐
    │ pending  │ ← cycle created, AI call in progress
    └────┬─────┘
         │
    ┌────┴─────────────────┐
    │                      │
    v                      v
┌───────────┐       ┌──────────┐
│ completed │       │  failed  │ ← AI parse error, API failure, etc.
└───────────┘       └──────────┘
```

### Roadmap Badge State

```text
roadmap_enabled=false → (no badge shown)

roadmap_enabled=true:
  ┌───────┐   queue empty + auto_launch   ┌──────────────┐
  │ Idle  │ ──────────────────────────────→│ Generating…  │
  └───────┘                                └──────┬───────┘
      ↑                                           │
      │              cycle completes               │
      │←──────────────────────────────────────────┘
      │                                           │
      │         items launched to pipeline         v
      │                                    ┌──────────┐
      └────────────────────────────────────│  Active  │
                pipeline completes          └──────────┘
```

## Validation Rules

| Rule | Scope | Error |
|------|-------|-------|
| `roadmap_batch_size` must be 1–10 | Config save | 422: "Batch size must be between 1 and 10" |
| `roadmap_seed` must be non-empty for generation | Generate trigger | 400: "Seed vision is required for generation" |
| `roadmap_seed` max 10,000 characters | Config save | 422: "Seed vision exceeds maximum length of 10,000 characters" |
| `roadmap_pipeline_id` must reference existing active pipeline | Generate trigger | 400: "Referenced pipeline does not exist or is not active" |
| `roadmap_grace_minutes` must be 0–1440 | Config save | 422: "Grace minutes must be between 0 and 1440" |
| AI response must parse as valid JSON array of RoadmapItems | Generation | Cycle marked as "failed", no items created |
| Daily auto-cycle count must be ≤ 10 | Auto-launch hook | Silently skipped, logged at INFO level |
| Debounce: last trigger must be ≥ 5 minutes ago | Auto-launch hook | Silently skipped, logged at DEBUG level |
