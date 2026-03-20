# Data Model: Undo/Redo Support for Destructive Actions

**Feature**: 054-undoable-delete
**Date**: 2026-03-20
**Status**: Complete

## Entities

### PendingDeletion

Represents a delete action confirmed by the user but not yet executed server-side. Exists only in client memory during the grace window.

| Field | Type | Description |
|-------|------|-------------|
| `entityId` | `string` | Unique identifier of the entity being deleted |
| `entityLabel` | `string` | Display name shown in the toast (e.g., "Agent: MyBot") |
| `timeoutId` | `NodeJS.Timeout` | Reference to the setTimeout that will fire the real delete |
| `toastId` | `string \| number` | Sonner toast identifier for programmatic dismissal |
| `cacheSnapshot` | `unknown` | Snapshot of TanStack Query cache data before optimistic removal |
| `queryKey` | `QueryKey` | TanStack Query key used to snapshot and restore cache |
| `onDelete` | `() => Promise<void>` | Callback that performs the actual API delete |
| `createdAt` | `number` | Timestamp (Date.now()) when the pending deletion was created |

**Lifecycle**: Created on delete trigger → Destroyed on undo, timer expiry, or component unmount.

**Validation Rules**:
- `entityId` must be non-empty string
- `onDelete` must be a function returning a Promise
- `queryKey` must be a valid TanStack Query key array
- Only one PendingDeletion per `entityId` at a time (re-deleting same entity resets timer)

### UndoToast

A transient UI notification tied to a PendingDeletion. Managed by sonner — no separate data structure needed. Configured via toast options.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Toast identifier (format: `undo-delete-${entityId}`) |
| `message` | `string` | Descriptive text (e.g., "Agent deleted") |
| `duration` | `number` | Auto-dismiss time in ms (default: 5000) |
| `action.label` | `string` | Button text: "Undo" |
| `action.onClick` | `() => void` | Callback that cancels deletion and restores item |

**Lifecycle**: Created with PendingDeletion → Dismissed on undo (replaced by "Restored" toast), timer expiry, or manual close.

## Relationships

```text
┌─────────────────┐        1:1        ┌──────────┐
│ PendingDeletion │───────────────────▶│ UndoToast│
│                 │  creates/controls  │ (sonner) │
└────────┬────────┘                    └──────────┘
         │
         │ references
         ▼
┌─────────────────┐
│  TanStack Query │
│   Cache Entry   │
│  (queryKey →    │
│   cached data)  │
└─────────────────┘
```

- One `PendingDeletion` creates exactly one `UndoToast`
- One `PendingDeletion` references one TanStack Query cache entry (for snapshot/restore)
- Multiple `PendingDeletion` instances can coexist (different `entityId` values)
- `PendingDeletion` instances are independent — no inter-entity relationships

## State Transitions

### PendingDeletion State Machine

```text
                    ┌──────────────┐
                    │              │
  delete trigger    │   PENDING    │
  ──────────────▶   │              │
                    │ • item hidden│
                    │ • toast shown│
                    │ • timer runs │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         user clicks   timer expires  component
           "Undo"         │           unmounts
              │            │            │
              ▼            ▼            ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │ RESTORED │  │ DELETING │  │ RESTORED │
       │          │  │          │  │ (silent) │
       │ • cache  │  │ • API    │  │          │
       │   restored│ │   DELETE │  │ • cache  │
       │ • toast: │  │   fires  │  │   restored│
       │  "Restored"│ │         │  │ • no toast│
       │ • timer  │  │         │  │ • timer  │
       │   cleared│  │         │  │   cleared│
       └──────────┘  └────┬─────┘  └──────────┘
                          │
                  ┌───────┼───────┐
                  │               │
             API success     API failure
                  │               │
                  ▼               ▼
           ┌──────────┐    ┌──────────┐
           │ DELETED  │    │ RESTORED │
           │          │    │          │
           │ • cache  │    │ • cache  │
           │   invalidated││   restored│
           │ • cleanup│    │ • error  │
           │          │    │   toast  │
           └──────────┘    └──────────┘
```

### State Descriptions

| State | Entry Condition | Actions | Exit Condition |
|-------|----------------|---------|----------------|
| **PENDING** | User confirms delete | Hide item (setQueryData), show undo toast, start setTimeout | User clicks Undo, timer expires, or component unmounts |
| **RESTORED** (user undo) | User clicks "Undo" in toast | Clear timeout, restore cache snapshot (setQueryData), show "Restored" toast, dismiss undo toast | Terminal — cleanup PendingDeletion entry |
| **RESTORED** (unmount) | Component unmounts during grace window | Clear timeout, restore cache snapshot, dismiss toast | Terminal — cleanup PendingDeletion entry |
| **DELETING** | Grace timer expires | Fire API DELETE call | API resolves (success or failure) |
| **DELETED** | API DELETE succeeds | Invalidate queries, cleanup PendingDeletion entry | Terminal |
| **RESTORED** (API error) | API DELETE fails | Restore cache snapshot, show error toast, cleanup PendingDeletion entry | Terminal |

## Entity-Specific Query Keys

The hook requires knowing which TanStack Query cache entries to snapshot and restore for each entity type.

| Entity | Query Key Pattern | Source File |
|--------|------------------|-------------|
| Agent | `['agents', 'list', projectId]` | `useAgents.ts` |
| Tool | `['tools', 'list', projectId]` | `useTools.ts` |
| Chore | `['chores', 'list', projectId]` | `useChores.ts` |
| Pipeline | `['pipelines', 'list', projectId]` | `usePipelineConfig.ts` |
| App | `['apps', 'list']` | `useApps.ts` |

## Data Integrity Constraints

1. **No duplicate pending IDs**: Only one PendingDeletion per `entityId` at any time. If the same entity is "deleted" again while pending, the existing timer is cleared and reset.
2. **Snapshot immutability**: Cache snapshots are captured once at delete trigger time and never modified. Restoration always uses the original snapshot.
3. **Cleanup guarantee**: Every code path (undo, timer expiry, unmount) must clear the PendingDeletion entry from the Map and the `pendingIds` Set.
4. **No orphaned timers**: `useEffect` cleanup iterates the entire Map and clears all timeouts.
5. **No server-side state**: PendingDeletion exists only in browser memory. Page refresh or tab close loses all pending deletions (items reappear from server on next fetch).
