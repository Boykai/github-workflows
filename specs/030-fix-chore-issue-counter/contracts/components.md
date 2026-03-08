# Component Contracts: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Feature**: 030-fix-chore-issue-counter | **Date**: 2026-03-08

## No New Components

This bug fix does not require any new frontend components.

---

## Modified Components

### ChoresPage (MODIFIED)

**Location**: `frontend/src/pages/ChoresPage.tsx`
**Purpose**: Top-level page that computes `parentIssueCount` and passes it to all chore components.

```typescript
// EXISTING interface — no changes
interface ChoresPageProps {
  // No props — uses hooks internally
}
```

**Behaviour Change**:

The `parentIssueCount` useMemo computation adds one additional filter condition:

```typescript
// Before (bug):
const parentIssueCount = useMemo(() => {
  // ... sub-issue collection ...
  for (const item of column.items ?? []) {
    if (item.content_type !== 'issue') continue;
    if (seenItemIds.has(item.item_id)) continue;
    if (item.number != null && subIssueNumbers.has(item.number)) continue;
    count += 1;  // ← Counts chore-labelled issues too
  }
}, [boardData]);

// After (fix):
const parentIssueCount = useMemo(() => {
  // ... sub-issue collection ...
  for (const item of column.items ?? []) {
    if (item.content_type !== 'issue') continue;
    if (seenItemIds.has(item.item_id)) continue;
    if (item.number != null && subIssueNumbers.has(item.number)) continue;
    if (item.labels?.some(l => l.name === 'chore')) continue;  // ← NEW: Skip chore issues
    count += 1;
  }
}, [boardData]);
```

**Impact**: All downstream consumers (`ChoresPanel`, `ChoreCard`, `FeaturedRitualsPanel`) receive the corrected count without any changes to their own code.

---

## Unchanged Components

### ChoreCard

**Location**: `frontend/src/components/chores/ChoreCard.tsx`
**Status**: No changes needed.

The `getNextTriggerInfo()` and `getTopRightTriggerLabel()` functions already correctly compute:
```typescript
const issuesSince = parentIssueCount - chore.last_triggered_count;
const remaining = Math.max(0, chore.schedule_value - issuesSince);
```

These functions are correct — they just need the corrected `parentIssueCount` input.

### FeaturedRitualsPanel

**Location**: `frontend/src/components/chores/FeaturedRitualsPanel.tsx`
**Status**: No changes needed.

The `computeRemaining()` function already correctly uses `parentIssueCount`:
```typescript
function computeRemaining(chore: Chore, parentIssueCount: number): number {
  const issuesSince = parentIssueCount - chore.last_triggered_count;
  return Math.max(0, chore.schedule_value - issuesSince);
}
```

### ChoresPanel

**Location**: `frontend/src/components/chores/ChoresPanel.tsx`
**Status**: No changes needed. Passes `parentIssueCount` through to `ChoreCard`.

---

## Data Flow Diagram

```
ChoresPage
  │
  ├─ useProjectBoard() → boardData
  │   │
  │   └─ parentIssueCount = useMemo(boardData)  ← FIX APPLIED HERE
  │       Filters: content_type=issue, NOT sub-issue, NOT chore-labelled, dedup
  │
  ├─ useChoresList() → chores
  │
  ├─ FeaturedRitualsPanel(chores, parentIssueCount)
  │   └─ computeRemaining(chore, parentIssueCount)  ← Receives corrected count
  │
  └─ ChoresPanel(projectId, parentIssueCount)
      └─ ChoreCard(chore, parentIssueCount)  ← Receives corrected count
          ├─ getNextTriggerInfo(chore, parentIssueCount)
          └─ getTopRightTriggerLabel(chore, parentIssueCount)
```
