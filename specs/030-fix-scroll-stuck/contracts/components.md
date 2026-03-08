# Component Contracts: Fix Screen Scrolling Getting Stuck Intermittently

## Overview

This is a frontend-only bug fix. No API changes are needed. The fix introduces a centralized scroll-lock hook and modifies 6 modal components to use it instead of independently manipulating `document.body.style.overflow`. Additionally, 4 components with capture-phase scroll listeners are updated to use passive listeners for improved scroll performance.

## New Hook

### useScrollLock

**Location**: `frontend/src/hooks/useScrollLock.ts`

```typescript
function useScrollLock(isLocked: boolean): void
```

**Contract**:

- When `isLocked` transitions from `false` to `true`: increments the global lock counter and sets `document.body.style.overflow = 'hidden'`
- When `isLocked` transitions from `true` to `false` (via cleanup): decrements the global lock counter
- When the lock counter reaches 0: restores `document.body.style.overflow` to its original value (captured before the first lock)
- Multiple simultaneous consumers are supported via reference counting
- The hook is idempotent for the same `isLocked` value across re-renders

**Usage**:

```typescript
import { useScrollLock } from '@/hooks/useScrollLock';

function MyModal({ isOpen }: { isOpen: boolean }) {
  useScrollLock(isOpen);
  // ... modal content
}
```

## Modified Components

### IssueDetailModal

**Location**: `frontend/src/components/board/IssueDetailModal.tsx`

**Before**:

- Single `useEffect` handles both keydown listener registration AND scroll lock
- Depends on `[handleKeyDown]` — re-runs on every render if `handleKeyDown` is not memoized
- Cleanup sets `document.body.style.overflow = ''` (not the previous value)

**After**:

- `useScrollLock(true)` — always locked when mounted (component is only rendered when modal is open)
- Separate `useEffect` for keydown listener only
- No direct manipulation of `document.body.style.overflow`

**Behavioral Change**: Scroll lock is managed by the centralized hook. Closing this modal no longer unconditionally resets body overflow — it only decrements the lock counter.

### CleanUpConfirmModal

**Location**: `frontend/src/components/board/CleanUpConfirmModal.tsx`

**Before**: Same pattern as IssueDetailModal — single useEffect, cleanup sets overflow to `''`.

**After**: `useScrollLock(true)` + separate keydown useEffect.

**Behavioral Change**: Same as IssueDetailModal.

### CleanUpSummary

**Location**: `frontend/src/components/board/CleanUpSummary.tsx`

**Before**: Same pattern.

**After**: `useScrollLock(true)` + separate keydown useEffect.

**Behavioral Change**: Same as IssueDetailModal.

### CleanUpAuditHistory

**Location**: `frontend/src/components/board/CleanUpAuditHistory.tsx`

**Before**: Same pattern.

**After**: `useScrollLock(true)` + separate keydown useEffect.

**Behavioral Change**: Same as IssueDetailModal.

### AgentIconPickerModal

**Location**: `frontend/src/components/agents/AgentIconPickerModal.tsx`

**Before**:

- `useEffect` with `[isOpen]` dependency
- Stores `previousOverflow` before setting `'hidden'`
- Restores `previousOverflow` on cleanup

**After**: `useScrollLock(isOpen)` — single line replacement.

**Behavioral Change**: Functionally equivalent for single-modal use. Improved for nested-modal scenarios due to reference counting.

### PipelineToolbar

**Location**: `frontend/src/components/pipeline/PipelineToolbar.tsx`

**Before**:

- Single `useEffect` handles scroll lock + Escape keydown listener
- Depends on `[showCopyDialog]`
- Stores `previousOverflow` before setting `'hidden'`
- Restores `previousOverflow` on cleanup

**After**:

- `useScrollLock(showCopyDialog)` — scroll lock in one line
- Separate `useEffect` for Escape keydown listener

**Behavioral Change**: Functionally equivalent for single-modal use. Improved separation of concerns.

## Scroll Listener Changes

### NotificationBell

**Location**: `frontend/src/layout/NotificationBell.tsx`

**Before**: `window.addEventListener('scroll', updatePosition, true)`
**After**: `window.addEventListener('scroll', updatePosition, { capture: true, passive: true })`

**Behavioral Change**: Browser can optimize scrolling because it knows the handler won't call `preventDefault()`. No visible behavior change.

### AddAgentPopover

**Location**: `frontend/src/components/board/AddAgentPopover.tsx`

**Before**: `window.addEventListener('scroll', onReposition, true)`
**After**: `window.addEventListener('scroll', onReposition, { capture: true, passive: true })`

**Behavioral Change**: Same as NotificationBell.

### ModelSelector

**Location**: `frontend/src/components/pipeline/ModelSelector.tsx`

**Before**: `window.addEventListener('scroll', updatePosition, true)`
**After**: `window.addEventListener('scroll', updatePosition, { capture: true, passive: true })`

**Behavioral Change**: Same as NotificationBell.

### StageCard

**Location**: `frontend/src/components/pipeline/StageCard.tsx`

**Before**: `window.addEventListener('scroll', updatePickerPosition, true)`
**After**: `window.addEventListener('scroll', updatePickerPosition, { capture: true, passive: true })`

**Behavioral Change**: Same as NotificationBell.

## No New API Endpoints

This is a frontend-only fix. No backend changes are needed.

## Regression Testing Surface

The following existing functionality must continue to work after the fix:

| Feature | Component(s) | Test |
|---------|-------------|------|
| Issue detail modal open/close | IssueDetailModal | Open issue, verify modal content, close, verify scroll works |
| Cleanup flow modal sequence | CleanUpConfirmModal → CleanUpSummary → CleanUpAuditHistory | Run full cleanup flow, verify scroll after each modal |
| Agent icon picker | AgentIconPickerModal | Open picker, scroll icon list, close, verify page scroll |
| Pipeline copy dialog | PipelineToolbar | Open copy dialog, press Escape, verify scroll works |
| Notification bell dropdown | NotificationBell | Open dropdown, scroll page, verify dropdown repositions |
| Agent popover | AddAgentPopover | Open popover, scroll, verify repositioning |
| Model selector dropdown | ModelSelector | Open selector, scroll, verify repositioning |
| Drag-and-drop agents | AgentConfigRow | Drag agent between columns, verify scroll during drag |
| Board column scrolling | BoardColumn | Scroll within a column, verify independence from page scroll |
| Chat interface scrolling | ChatInterface | Scroll chat messages, verify smooth scrolling |
