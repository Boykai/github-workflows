# Data Model: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Feature**: 030-fix-chore-issue-counter | **Date**: 2026-03-08

## Backend Entities (No Changes)

### Chore (UNCHANGED)

The existing `Chore` model already contains all fields necessary for the counter fix. No schema changes are required.

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
    last_triggered_count: int = 0             # Parent issue count at last trigger (counter baseline)
    current_issue_number: int | None = None   # Open instance (1-open constraint)
    current_issue_node_id: str | None = None  # GraphQL node ID of open instance
    pr_number: int | None = None              # Template commit PR number
    pr_url: str | None = None                 # Template commit PR URL
    tracking_issue_number: int | None = None  # Setup tracking issue number
    execution_count: int = 0                  # All-time trigger execution count
    ai_enhance_enabled: bool = True           # AI Enhance toggle state
    agent_pipeline_id: str = ""               # Pipeline config ID ("" = Auto)
    created_at: str                           # ISO 8601 datetime
    updated_at: str                           # ISO 8601 datetime
```

**Key Fields for Counter Fix**:
- `schedule_type`: Must be `"count"` for the "Every X Issues" trigger.
- `schedule_value`: The threshold (e.g., 5 for "Every 5 issues").
- `last_triggered_count`: Snapshot of the global qualifying parent issue count at the time this Chore last fired. Each Chore has its own value, enabling independent scoping.

**Counter Formula**: `remaining = max(0, schedule_value - (parentIssueCount - last_triggered_count))`

---

## Frontend Types (No Changes)

### BoardItem (UNCHANGED)

The `BoardItem` type already includes `labels` which provides the data needed for chore-label filtering.

```typescript
interface BoardItem {
  item_id: string;
  content_id?: string;
  content_type: ContentType;   // "issue" | "pr" | "draft"
  title: string;
  number?: number;
  labels: BoardLabel[];        // ← Used for chore-label exclusion
  sub_issues: SubIssue[];      // ← Used for sub-issue exclusion
  // ... other fields
}

interface BoardLabel {
  id: string;
  name: string;                // ← Check for "chore" label
  color: string;
}

interface SubIssue {
  id: string;
  number: number;
  title: string;
  // ... other fields
}
```

---

## Derived Data: Qualifying Parent Issue Count

### Definition

A **Qualifying Parent Issue** is a `BoardItem` that meets ALL of the following criteria:

1. `content_type === 'issue'` — only GitHub Issues, not PRs or draft issues
2. Not a Sub-Issue — `item.number` is NOT in the set of all `subIssue.number` values across all parent items
3. **Not a Chore** — `item.labels` does NOT contain a label with `name === 'chore'`
4. Unique — deduplicated by `item_id` (an item may appear in multiple board column snapshots)

### Computation Location

**File**: `frontend/src/pages/ChoresPage.tsx` — `parentIssueCount` useMemo

### Data Flow

```text
useProjectBoard() → boardData.columns[*].items[*]
    │
    ├─ Pass 1: Collect subIssueNumbers from all items' sub_issues arrays
    │
    └─ Pass 2: For each item in all columns:
         ├─ Skip if content_type !== 'issue'
         ├─ Skip if already seen (dedup by item_id)
         ├─ Skip if number ∈ subIssueNumbers          ← Sub-Issue exclusion (existing)
         ├─ Skip if labels.some(l => l.name === 'chore') ← Chore exclusion (NEW)
         └─ Increment count
```

### Consumers

The `parentIssueCount` value flows to these consumers (all unchanged):

| Consumer | File | Usage |
|----------|------|-------|
| `ChoreCard` | `frontend/src/components/chores/ChoreCard.tsx:60-64` | Tile counter: `remaining = schedule_value - (parentIssueCount - last_triggered_count)` |
| `ChoreCard` | `frontend/src/components/chores/ChoreCard.tsx:83-86` | Top-right badge: `remaining/schedule_value` |
| `FeaturedRitualsPanel` | `frontend/src/components/chores/FeaturedRitualsPanel.tsx:27-30` | "Next Run" ranking computation |
| `evaluate_count_trigger` | `backend/src/services/chores/counter.py:22` | Trigger evaluation: `issues_since = current_count - last_triggered_count` |

---

## State Transitions

### Chore Counter Lifecycle

```
┌─────────────────┐
│  Chore Created   │  last_triggered_count = 0 (or should be parentIssueCount at creation)
│  Never Executed  │  Counter shows: parentIssueCount - 0 = all qualifying issues
└────────┬────────┘
         │  qualifyingParentIssueCount >= schedule_value
         ▼
┌─────────────────┐
│  Chore Triggers  │  last_triggered_count ← parentIssueCount (snapshot)
│  Counter Resets  │  Counter shows: parentIssueCount - parentIssueCount = 0
└────────┬────────┘
         │  new qualifying Parent Issues created
         ▼
┌─────────────────┐
│  Counter Growing │  Counter shows: parentIssueCount - last_triggered_count
│  (0 < n < threshold) │
└────────┬────────┘
         │  qualifyingParentIssueCount - last_triggered_count >= schedule_value
         ▼
┌─────────────────┐
│  Threshold Met   │  Counter shows: "Ready to trigger" (remaining = 0)
│  Awaiting Trigger│  Trigger evaluation returns True
└────────┬────────┘
         │  trigger fires
         ▼
         (back to "Chore Triggers / Counter Resets")
```

---

## Validation Rules

| Rule | Location | Description |
|------|----------|-------------|
| `schedule_type = 'count'` required | `counter.py:19`, `ChoreCard.tsx:60` | Counter logic only applies to count-based schedules |
| `schedule_value > 0` | `chores.py` model validation, `010_chores.sql` CHECK | Threshold must be positive |
| `parentIssueCount >= 0` | `ChoresPage.tsx` memo | Count cannot be negative |
| `last_triggered_count >= 0` | Database DEFAULT 0 | Baseline cannot be negative |
| Chore label = `"chore"` (case-sensitive) | `service.py:372`, `ChoresPage.tsx` filter | Must match the exact label applied at issue creation |
