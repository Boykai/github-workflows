# Data Model: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Feature**: 029-chores-page-enhancements | **Date**: 2026-03-07

## Backend Entities (Pydantic Models)

### Chore (MODIFIED)

Extended with execution tracking, AI enhance preference, and pipeline assignment.

```python
class Chore(BaseModel):
    """A recurring task definition with scheduling and execution tracking."""

    id: str                                   # UUID, primary key
    project_id: str                           # GitHub Project node ID
    name: str                                 # Unique per project (1–200 chars)
    template_path: str                        # .github/ISSUE_TEMPLATE/chore-*.md
    template_content: str                     # Full markdown with YAML front matter
    schedule_type: ScheduleType | None = None # "time" or "count" or None
    schedule_value: int | None = None         # Days or issue count threshold
    status: ChoreStatus = ChoreStatus.ACTIVE  # "active" or "paused"
    last_triggered_at: str | None = None      # ISO 8601 datetime of last trigger
    last_triggered_count: int = 0             # Parent issue count at last trigger
    current_issue_number: int | None = None   # Open instance (1-open constraint)
    current_issue_node_id: str | None = None  # GraphQL node ID of open instance
    pr_number: int | None = None              # Template commit PR number
    pr_url: str | None = None                 # Template commit PR URL
    tracking_issue_number: int | None = None  # Setup tracking issue number
    execution_count: int = 0                  # NEW: All-time trigger execution count
    ai_enhance_enabled: bool = True           # NEW: AI Enhance toggle state (default ON)
    agent_pipeline_id: str = ""               # NEW: Pipeline config ID ("" = Auto)
    created_at: str                           # ISO 8601 datetime
    updated_at: str                           # ISO 8601 datetime
```

**New Fields**:
- `execution_count`: All-time count of how many times this Chore has been triggered. Incremented by 1 on each successful trigger in `trigger_chore()`. Used for "Most Run" ranking in the Featured Rituals panel. Default 0 for existing Chores.
- `ai_enhance_enabled`: Whether the AI Enhance toggle is ON (true) or OFF (false) for this Chore. When OFF, the Chore's chat flow generates metadata-only and uses the user's raw input as the template body. Default true (ON) for existing Chores.
- `agent_pipeline_id`: Reference to a saved `pipeline_configs.id`. Empty string means "Auto" — resolve to the project's active pipeline at execution time via `project_settings.assigned_pipeline_id`. Default empty string for existing Chores.

**Validation Rules**:
- `execution_count` must be >= 0 (enforced by database CHECK constraint)
- `agent_pipeline_id` must be a valid UUID string or empty string (format check; existence check is advisory — pipeline may be deleted after Chore save)

### ChoreUpdate (MODIFIED)

Extended to support AI enhance and pipeline configuration updates.

```python
class ChoreUpdate(BaseModel):
    """Request body for updating a Chore's schedule, status, and configuration."""

    schedule_type: ScheduleType | None = None
    schedule_value: int | None = Field(default=None, gt=0)
    status: ChoreStatus | None = None
    ai_enhance_enabled: bool | None = None       # NEW: Toggle AI Enhance
    agent_pipeline_id: str | None = None          # NEW: Set pipeline ("" = Auto)
```

### ChoreInlineUpdate (NEW)

```python
class ChoreInlineUpdate(BaseModel):
    """Request body for inline editing of a Chore definition. Creates a PR on save."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    template_content: str | None = Field(default=None, min_length=1)
    schedule_type: ScheduleType | None = None
    schedule_value: int | None = Field(default=None, gt=0)
    ai_enhance_enabled: bool | None = None
    agent_pipeline_id: str | None = None
    expected_sha: str | None = None              # Optimistic concurrency: file SHA at load time
```

**Fields**:
- All fields optional — only changed fields are sent.
- `expected_sha`: SHA of the template file when the page was loaded. Used for conflict detection (see R12 in research.md). If the file has been modified since load, the endpoint returns 409 Conflict.

### ChoreInlineUpdateResponse (NEW)

```python
class ChoreInlineUpdateResponse(BaseModel):
    """Response from inline Chore update with PR creation result."""

    chore: Chore                               # Updated Chore record
    pr_number: int | None = None               # PR number if created
    pr_url: str | None = None                  # PR URL if created
    pr_merged: bool = False                    # Whether auto-merge succeeded (new Chores only)
    merge_error: str | None = None             # Error message if auto-merge failed
```

### ChoreCreateWithConfirmation (NEW)

```python
class ChoreCreateWithConfirmation(BaseModel):
    """Request body for creating a new Chore with the full auto-merge flow."""

    name: str = Field(..., min_length=1, max_length=200)
    template_content: str = Field(..., min_length=1)
    ai_enhance_enabled: bool = True
    agent_pipeline_id: str = ""
    auto_merge: bool = True                    # Whether to auto-merge the PR into main
```

### ChoreCreateResponse (NEW)

```python
class ChoreCreateResponse(BaseModel):
    """Response from Chore creation with full flow result."""

    chore: Chore                               # Created Chore record
    issue_number: int | None = None            # Tracking issue number
    pr_number: int | None = None               # PR number
    pr_url: str | None = None                  # PR URL
    pr_merged: bool = False                    # Whether auto-merge succeeded
    merge_error: str | None = None             # Error message if auto-merge failed
```

### ChoreChatMessage (MODIFIED)

Extended with AI enhance flag.

```python
class ChoreChatMessage(BaseModel):
    """Request body for Chore chat (sparse input refinement)."""

    content: str
    conversation_id: str | None = None
    ai_enhance: bool = True                    # NEW: Controls metadata-only vs. full generation
```

### FeaturedRituals (NEW — Frontend Only)

This is a derived view, not a backend model. Included here for completeness.

```python
# Not a backend model — computed on the frontend from the Chore list.
# Documented here for cross-reference with data-model.md and contracts/components.md.
```

---

## Frontend Types (TypeScript)

### Chore Type (MODIFIED)

```typescript
interface Chore {
  id: string;
  project_id: string;
  name: string;
  template_path: string;
  template_content: string;
  schedule_type: ScheduleType | null;
  schedule_value: number | null;
  status: ChoreStatus;
  last_triggered_at: string | null;
  last_triggered_count: number;
  current_issue_number: number | null;
  current_issue_node_id: string | null;
  pr_number: number | null;
  pr_url: string | null;
  tracking_issue_number: number | null;
  execution_count: number;             // NEW: All-time execution count
  ai_enhance_enabled: boolean;         // NEW: AI Enhance toggle state
  agent_pipeline_id: string;           // NEW: Pipeline config ID ("" = Auto)
  created_at: string;
  updated_at: string;
}
```

### ChoreUpdate Type (MODIFIED)

```typescript
interface ChoreUpdate {
  schedule_type?: ScheduleType | null;
  schedule_value?: number | null;
  status?: ChoreStatus;
  ai_enhance_enabled?: boolean;        // NEW
  agent_pipeline_id?: string;          // NEW
}
```

### New Types

```typescript
// Inline edit request body
interface ChoreInlineUpdate {
  name?: string;
  template_content?: string;
  schedule_type?: ScheduleType | null;
  schedule_value?: number | null;
  ai_enhance_enabled?: boolean;
  agent_pipeline_id?: string;
  expected_sha?: string;               // Optimistic concurrency token
}

// Inline edit response
interface ChoreInlineUpdateResponse {
  chore: Chore;
  pr_number: number | null;
  pr_url: string | null;
  pr_merged: boolean;
  merge_error: string | null;
}

// Full creation request with auto-merge flag
interface ChoreCreateWithConfirmation {
  name: string;
  template_content: string;
  ai_enhance_enabled: boolean;
  agent_pipeline_id: string;
  auto_merge: boolean;
}

// Full creation response
interface ChoreCreateResponse {
  chore: Chore;
  issue_number: number | null;
  pr_number: number | null;
  pr_url: string | null;
  pr_merged: boolean;
  merge_error: string | null;
}

// Chat message with AI enhance flag
interface ChoreChatMessage {
  content: string;
  conversation_id?: string;
  ai_enhance?: boolean;                // NEW: Controls generation mode
}

// Featured Rituals panel data (derived client-side)
interface FeaturedRituals {
  nextRun: FeaturedRitualCard | null;
  mostRecentlyRun: FeaturedRitualCard | null;
  mostRun: FeaturedRitualCard | null;
}

// Individual Featured Ritual card data
interface FeaturedRitualCard {
  choreId: string;
  choreName: string;
  stat: string;                        // e.g., "2 issues remaining", "Run 3h ago", "15 runs"
  statValue: number;                   // Numeric value for sorting
}

// Chore edit dirty state tracking
interface ChoreEditState {
  original: Chore;
  current: Partial<ChoreInlineUpdate>;
  isDirty: boolean;
  fileSha: string | null;              // Template file SHA for conflict detection
}

// Per-Chore counter display data
interface ChoreCounterData {
  choreId: string;
  remaining: number;                   // schedule_value - issues_since
  totalThreshold: number;              // schedule_value
  issuesSinceLastRun: number;          // current_count - last_triggered_count
}
```

### Existing Types (UNCHANGED)

```typescript
// These types are unchanged from the initial Chores implementation
type ScheduleType = 'time' | 'count';
type ChoreStatus = 'active' | 'paused';

interface ChoreTemplate {
  name: string;
  about: string;
  path: string;
  content: string;
}

interface ChoreTriggerResult {
  chore_id: string;
  chore_name: string;
  triggered: boolean;
  issue_number: number | null;
  issue_url: string | null;
  skip_reason: string | null;
}

// PipelineConfigSummary from spec 028 — used in PipelineSelector dropdown
interface PipelineConfigSummary {
  id: string;
  name: string;
  description: string;
  stageCount: number;
  agentCount: number;
  // ... other fields from spec 028
}
```

---

## Database Schema

### Migration 016: Chores Enhancements

```sql
-- 016_chores_enhancements.sql
-- Extends chores table with execution tracking, AI enhance preference, and pipeline assignment.

-- Add execution count for "Most Run" ranking
ALTER TABLE chores ADD COLUMN execution_count INTEGER NOT NULL DEFAULT 0;

-- Add AI enhance toggle (1 = ON/default, 0 = OFF)
ALTER TABLE chores ADD COLUMN ai_enhance_enabled INTEGER NOT NULL DEFAULT 1;

-- Add agent pipeline reference ("" = Auto, UUID = specific pipeline)
ALTER TABLE chores ADD COLUMN agent_pipeline_id TEXT NOT NULL DEFAULT '';

-- Add check constraint for execution_count
-- Note: SQLite doesn't support ALTER TABLE ADD CONSTRAINT, so this is enforced at the application level.
-- The existing CHECK constraints on schedule_type/schedule_value remain unchanged.

-- Index for Featured Rituals queries (Most Run ranking, Most Recently Run)
CREATE INDEX IF NOT EXISTS idx_chores_execution_count ON chores(execution_count DESC);
CREATE INDEX IF NOT EXISTS idx_chores_last_triggered_at ON chores(last_triggered_at DESC);
```

**Notes**:
- `execution_count`: Default 0 for all existing Chores. Incremented atomically in `trigger_chore()` via `UPDATE chores SET execution_count = execution_count + 1 WHERE id = ?`.
- `ai_enhance_enabled`: SQLite boolean (0/1). Default 1 (ON) to preserve existing behavior for all current Chores.
- `agent_pipeline_id`: Default empty string = "Auto". Not a foreign key constraint — allows graceful handling if referenced pipeline is deleted (see R11 in research.md).
- Indexes on `execution_count` and `last_triggered_at` optimize the Featured Rituals panel's ranking queries, though with small Chore counts these are primarily for correctness of sort order.

---

## State Machines

### Chore Inline Edit Flow

```
User views ChoresPage
    │
    ▼
ChoreCard renders fields as editable inputs (default state)
    │
    ├─ User modifies a field
    │   │
    │   ▼
    │  ChoresPanel.editState[choreId].isDirty = true
    │  Dirty-state indicator appears (banner or asterisk)
    │  Save button becomes prominent
    │   │
    │   ├─ User clicks Save
    │   │   │
    │   │   ▼
    │   │  PUT /chores/{projectId}/{choreId}/inline-update
    │   │   │
    │   │   ├─ 200 OK → PR created
    │   │   │   ├─ editState cleared, isDirty = false
    │   │   │   └─ Toast: "PR #{num} created with your changes"
    │   │   │
    │   │   ├─ 409 Conflict → File modified since load
    │   │   │   └─ Show conflict modal: "File changed. Overwrite or Reload?"
    │   │   │
    │   │   └─ 4xx/5xx → Error
    │   │       └─ Toast: error message, edit state preserved
    │   │
    │   ├─ User navigates away
    │   │   │
    │   │   ▼
    │   │  useUnsavedChanges hook triggers
    │   │  Confirmation dialog: "You have unsaved changes — discard?"
    │   │   │
    │   │   ├─ "Stay" → user returns to editing
    │   │   └─ "Discard" → editState cleared, navigation proceeds
    │   │
    │   └─ User clicks Discard/Reset
    │       │
    │       ▼
    │      editState[choreId] reset to original values
    │      isDirty = false
    │
    └─ User doesn't modify anything → no dirty state
```

### New Chore Creation with Double Confirmation & Auto-Merge

```
User clicks "Add Chore" in AddChoreModal
    │
    ▼
AddChoreModal: sparse input detection
    │
    ├─ Sparse input → ChoreChatFlow (multi-turn refinement)
    │   │
    │   └─ Template ready → proceed to confirmation
    │
    └─ Complete input → proceed directly to confirmation
        │
        ▼
ConfirmChoreModal: Step 1 (Information)
"This will add a Chore file to your repository and auto-merge a PR into main."
    │
    ├─ "Cancel" → return to AddChoreModal (input preserved)
    │
    └─ "I Understand, Continue"
        │
        ▼
    ConfirmChoreModal: Step 2 (Final Confirmation)
    "Create this Chore? Issue + PR + auto-merge into main."
        │
        ├─ "Back" → return to Step 1
        │
        └─ "Yes, Create Chore"
            │
            ▼
        POST /chores/{projectId} (with auto_merge=true)
            │
            ├─ Step 1: Create branch + commit template file
            ├─ Step 2: Create PR
            ├─ Step 3: Create tracking issue
            ├─ Step 4: Merge PR (squash)
            │   │
            │   ├─ Merge success → pr_merged=true
            │   │   └─ Toast: "Chore created and merged into main ✓"
            │   │
            │   └─ Merge failure → pr_merged=false, merge_error="..."
            │       └─ Toast: "Chore created but PR needs manual merge" + link
            │
            └─ Step 5: Persist Chore record locally (always, even if merge fails)
                │
                ▼
            Modal closes, ChoresPanel refreshes
```

### AI Enhance Toggle Flow

```
User opens AddChoreModal or enters ChoreCard edit mode
    │
    ▼
AI Enhance toggle visible (default: ON, or Chore's saved preference)
    │
    ├─ AI Enhance ON (default)
    │   │
    │   ▼
    │  ChoreChatFlow: full AI generation
    │  AI generates both YAML front matter AND body content
    │  (existing behavior, no change)
    │
    └─ AI Enhance OFF
        │
        ▼
       ChoreChatFlow: metadata-only generation
       User's chat input → locked as template body (verbatim)
       AI generates ONLY: name, about, title, labels, assignees
       Final template = AI front matter + user's raw body
```

### Agent Pipeline Selection Flow

```
User opens PipelineSelector dropdown (ChoreCard or AddChoreModal)
    │
    ▼
Dropdown shows:
├── "Auto" (default, inherits project pipeline)
├── "Spec Kit" (if preset exists)
├── "GitHub Copilot" (if preset exists)
├── [User-saved pipelines...]
    │
    ├─ User selects "Auto"
    │   └─ agent_pipeline_id = "" (empty)
    │
    └─ User selects a specific pipeline
        └─ agent_pipeline_id = pipeline.id
            │
            ▼
        At execution time (trigger_chore):
            │
            ├─ agent_pipeline_id non-empty
            │   └─ Fetch pipeline_configs WHERE id = agent_pipeline_id
            │       ├─ Found → use this pipeline
            │       └─ Not found → fall back to Auto + warn user (FR-017)
            │
            └─ agent_pipeline_id empty ("Auto")
                └─ Read project_settings.assigned_pipeline_id
                    ├─ Non-empty → use project pipeline
                    └─ Empty → default workflow orchestrator (no pipeline override)
```

---

## Existing Entities (Referenced, Not Modified)

The following existing entities are referenced but their database tables/schemas are NOT modified:

- **pipeline_configs** (`backend/src/models/pipeline.py`, `backend/src/migrations/013_pipeline_configs.sql`, `015_pipeline_mcp_presets.sql`): Saved pipeline configurations. Referenced by `Chore.agent_pipeline_id`. Used to populate the `PipelineSelector` dropdown.
- **project_settings** (`backend/src/migrations/001_initial_schema.sql`, `015_pipeline_mcp_presets.sql`): Project-level settings including `assigned_pipeline_id`. Read at Chore trigger time for "Auto" pipeline resolution.
- **ChatMessageRequest** (`backend/src/models/chat.py`): Chat message model with `ai_enhance: bool` field. Referenced for consistency but NOT modified — the Chore chat uses its own `ChoreChatMessage` model.
- **Board items** (frontend `useProjectBoard()` hook): Used to compute parent issue count for counter display. Not modified.
