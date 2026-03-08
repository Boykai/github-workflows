# Data Model: Fix Screen Scrolling Getting Stuck Intermittently

## Overview

This feature is a bug fix — no new data entities are introduced. The fix is entirely behavioral: it changes how scroll-locking state is managed across modal components. This document captures the relevant state model and the behavioral changes.

## Scroll Lock State Model (New)

### Module-Level State: `useScrollLock`

**Location**: `frontend/src/hooks/useScrollLock.ts` (NEW)

```typescript
// Module-level singleton state (shared across all hook consumers)
let lockCount: number = 0;         // Number of active scroll locks
let originalOverflow: string = ''; // Original document.body.style.overflow before first lock
```

**State Transitions**:

```text
[No locks]                    [1+ locks active]
lockCount = 0                 lockCount > 0
overflow = originalOverflow   overflow = 'hidden'
        │                              │
        │  useScrollLock(true)         │  useScrollLock(true)
        │  ─────────────────►          │  ────────────────────►  lockCount++
        │  save originalOverflow       │  (no overflow change)
        │  set overflow = 'hidden'     │
        │  lockCount = 1               │
        │                              │
        │                              │  useScrollLock cleanup
        │  useScrollLock cleanup       │  ────────────────────►  lockCount--
        │  ◄─────────────────          │  (no overflow change
        │  lockCount = 0               │   if lockCount > 0)
        │  restore originalOverflow    │
        │                              │
```

### Invariants

1. `lockCount >= 0` — never negative
2. When `lockCount === 0`, `document.body.style.overflow` equals the value it had before the first lock was acquired
3. When `lockCount > 0`, `document.body.style.overflow === 'hidden'`
4. `originalOverflow` is only captured when transitioning from `lockCount === 0` to `lockCount === 1`
5. `originalOverflow` is only applied when transitioning from `lockCount === 1` to `lockCount === 0`

## Component Behavioral Changes

### Modal Components (Modified — scroll lock replaced)

The following components currently manage their own scroll lock via inline `useEffect`. All will be modified to use the centralized `useScrollLock` hook:

#### IssueDetailModal (Modified)

**Location**: `frontend/src/components/board/IssueDetailModal.tsx`

**Current Behavior** (lines 51–59):

```typescript
useEffect(() => {
  document.addEventListener('keydown', handleKeyDown);
  document.body.style.overflow = 'hidden';
  return () => {
    document.removeEventListener('keydown', handleKeyDown);
    document.body.style.overflow = '';
  };
}, [handleKeyDown]);
```

**New Behavior**:

```typescript
useScrollLock(true); // Always locked when mounted (modal is always open when rendered)

useEffect(() => {
  document.addEventListener('keydown', handleKeyDown);
  return () => {
    document.removeEventListener('keydown', handleKeyDown);
  };
}, [handleKeyDown]);
```

#### CleanUpConfirmModal (Modified)

**Location**: `frontend/src/components/board/CleanUpConfirmModal.tsx`

**Current Behavior** (lines 24–31): Same pattern as IssueDetailModal — sets overflow to `''` on cleanup.

**New Behavior**: Same pattern — `useScrollLock(true)` + separate keydown effect.

#### CleanUpSummary (Modified)

**Location**: `frontend/src/components/board/CleanUpSummary.tsx`

**Current Behavior** (lines 27–34): Same pattern.

**New Behavior**: Same pattern — `useScrollLock(true)` + separate keydown effect.

#### CleanUpAuditHistory (Modified)

**Location**: `frontend/src/components/board/CleanUpAuditHistory.tsx`

**Current Behavior** (lines 22–29): Same pattern.

**New Behavior**: Same pattern — `useScrollLock(true)` + separate keydown effect.

#### AgentIconPickerModal (Modified)

**Location**: `frontend/src/components/agents/AgentIconPickerModal.tsx`

**Current Behavior** (lines 23–34):

```typescript
useEffect(() => {
  if (!isOpen) return undefined;
  const previousOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  return () => {
    document.body.style.overflow = previousOverflow;
  };
}, [isOpen]);
```

**New Behavior**:

```typescript
useScrollLock(isOpen);
```

#### PipelineToolbar (Modified)

**Location**: `frontend/src/components/pipeline/PipelineToolbar.tsx`

**Current Behavior** (lines 55–72):

```typescript
useEffect(() => {
  if (!showCopyDialog) return undefined;
  const previousOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  const handleEscape = (event: KeyboardEvent) => { ... };
  window.addEventListener('keydown', handleEscape);
  return () => {
    document.body.style.overflow = previousOverflow;
    window.removeEventListener('keydown', handleEscape);
  };
}, [showCopyDialog]);
```

**New Behavior**:

```typescript
useScrollLock(showCopyDialog);

useEffect(() => {
  if (!showCopyDialog) return undefined;
  const handleEscape = (event: KeyboardEvent) => { ... };
  window.addEventListener('keydown', handleEscape);
  return () => {
    window.removeEventListener('keydown', handleEscape);
  };
}, [showCopyDialog]);
```

## Scroll Event Listener Changes

### Passive Listener Upgrade

The following components register capture-phase scroll listeners for popover repositioning. These are modified to include `passive: true`:

| Component | File | Current | New |
|-----------|------|---------|-----|
| NotificationBell | `layout/NotificationBell.tsx` | `addEventListener('scroll', fn, true)` | `addEventListener('scroll', fn, { capture: true, passive: true })` |
| AddAgentPopover | `components/board/AddAgentPopover.tsx` | `addEventListener('scroll', fn, true)` | `addEventListener('scroll', fn, { capture: true, passive: true })` |
| ModelSelector | `components/pipeline/ModelSelector.tsx` | `addEventListener('scroll', fn, true)` | `addEventListener('scroll', fn, { capture: true, passive: true })` |
| StageCard | `components/pipeline/StageCard.tsx` | `addEventListener('scroll', fn, true)` | `addEventListener('scroll', fn, { capture: true, passive: true })` |

**Note**: The `removeEventListener` calls must also be updated to use `{ capture: true }` to correctly remove the listener. The `passive` flag is not needed for removal.

## Validation Rules

No new validation rules. The scroll-lock state is managed entirely in memory with module-level variables. No persistence, no serialization, no API calls.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Two modals open simultaneously | `lockCount = 2`, overflow = 'hidden' |
| Inner modal closes first | `lockCount = 1`, overflow remains 'hidden' |
| Outer modal then closes | `lockCount = 0`, overflow restored to original |
| Modal opens during drag-and-drop | Scroll lock applies normally; drag continues in locked container |
| Browser tab switch and return | Scroll state is preserved (module-level variables persist) |
| Component unmount without cleanup (crash) | `lockCount` may be permanently incremented — mitigated by lockCount being module-level and resetting on page refresh |
| Rapid open/close of same modal | Each open increments, each close decrements — always converges to correct state |
