# Quickstart: Fix Screen Scrolling Getting Stuck Intermittently

## Prerequisites

- Node.js 22+ and npm
- Feature branch: `git checkout 030-fix-scroll-stuck` (or the working PR branch)

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

### Backend (for full integration testing)

```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

## Files to Create

| File | Description |
|------|-------------|
| `frontend/src/hooks/useScrollLock.ts` | **NEW**: Centralized scroll-lock hook with reference-counting |

## Files to Modify

| File | Change Type | Description |
|------|------------|-------------|
| `frontend/src/components/board/IssueDetailModal.tsx` | **Modify** | Replace manual scroll lock with `useScrollLock(true)`, separate keydown effect |
| `frontend/src/components/board/CleanUpConfirmModal.tsx` | **Modify** | Replace manual scroll lock with `useScrollLock(true)`, separate keydown effect |
| `frontend/src/components/board/CleanUpSummary.tsx` | **Modify** | Replace manual scroll lock with `useScrollLock(true)`, separate keydown effect |
| `frontend/src/components/board/CleanUpAuditHistory.tsx` | **Modify** | Replace manual scroll lock with `useScrollLock(true)`, separate keydown effect |
| `frontend/src/components/agents/AgentIconPickerModal.tsx` | **Modify** | Replace manual scroll lock with `useScrollLock(isOpen)` |
| `frontend/src/components/pipeline/PipelineToolbar.tsx` | **Modify** | Replace manual scroll lock with `useScrollLock(showCopyDialog)`, separate keydown effect |
| `frontend/src/layout/NotificationBell.tsx` | **Modify** | Add `passive: true` to capture-phase scroll listener |
| `frontend/src/components/board/AddAgentPopover.tsx` | **Modify** | Add `passive: true` to capture-phase scroll listener |
| `frontend/src/components/pipeline/ModelSelector.tsx` | **Modify** | Add `passive: true` to capture-phase scroll listener |
| `frontend/src/components/pipeline/StageCard.tsx` | **Modify** | Add `passive: true` to capture-phase scroll listener |

## Files That May Need Test Updates

| File | Change Type | Description |
|------|------------|-------------|
| `frontend/src/hooks/__tests__/useScrollLock.test.ts` | **Create** | Unit tests for `useScrollLock` hook — reference counting, nested modals, cleanup |

## Implementation Order

### Step 1: Create the useScrollLock Hook

**File**: `frontend/src/hooks/useScrollLock.ts`

Create a new hook with module-level reference counting:

```typescript
import { useEffect } from 'react';

let lockCount = 0;
let originalOverflow = '';

export function useScrollLock(isLocked: boolean): void {
  useEffect(() => {
    if (!isLocked) return;

    if (lockCount === 0) {
      originalOverflow = document.body.style.overflow;
    }
    lockCount++;
    document.body.style.overflow = 'hidden';

    return () => {
      lockCount--;
      if (lockCount === 0) {
        document.body.style.overflow = originalOverflow;
      }
    };
  }, [isLocked]);
}
```

**Verification**: Run `cd frontend && npx vitest run` to ensure no existing tests break.

### Step 2: Update Modal Components to Use useScrollLock

For each of the 6 modal components listed above:

1. Import `useScrollLock` from `@/hooks/useScrollLock`
2. Replace the manual `document.body.style.overflow` manipulation with `useScrollLock(isOpen)` (or `useScrollLock(true)` for always-open-when-mounted modals)
3. Separate keydown listener registration into its own `useEffect` if currently combined with scroll lock
4. Remove the `document.body.style.overflow` lines from the existing `useEffect`

**Verification**: For each modified component:

1. Open the modal in the UI
2. Verify the body scroll is locked (page behind modal doesn't scroll)
3. Close the modal
4. Verify the page scrolls normally

### Step 3: Update Scroll Event Listeners to Use Passive Option

For each of the 4 components with capture-phase scroll listeners:

1. Change `addEventListener('scroll', handler, true)` to `addEventListener('scroll', handler, { capture: true, passive: true })`
2. Change `removeEventListener('scroll', handler, true)` to `removeEventListener('scroll', handler, { capture: true })` (passive not needed for removal)

**Verification**: Open each component (notification bell, agent popover, model selector, stage card) and scroll the page — verify the popover/dropdown repositions correctly.

### Step 4: Test Nested Modal Scenarios

1. Navigate to the Board page
2. Click an issue to open `IssueDetailModal`
3. While the modal is open, trigger any action that opens a second modal (if possible)
4. Close the inner modal — verify the page is still scroll-locked (outer modal still open)
5. Close the outer modal — verify the page scrolls normally
6. Repeat with the cleanup flow: `CleanUpConfirmModal` → `CleanUpSummary` → `CleanUpAuditHistory`

### Step 5: Run Full Test Suite

```bash
cd frontend
npx vitest run
```

Verify all existing tests pass.

### Step 6: Cross-Browser Verification

Test the fix in:

- [ ] Chrome (desktop)
- [ ] Firefox (desktop)
- [ ] Safari (desktop)
- [ ] Mobile device (touch scrolling)

For each browser:

1. Navigate to any scrollable page
2. Scroll up and down rapidly — verify no freezing
3. Open and close modals — verify scroll restores correctly
4. Switch browser tabs and return — verify scroll works

## Verification Checklist

- [ ] New `useScrollLock` hook created with reference counting
- [ ] All 6 modal components use `useScrollLock` instead of manual overflow manipulation
- [ ] Keydown handlers separated into their own `useEffect` in all modified modals
- [ ] All 4 scroll listeners updated with `passive: true`
- [ ] Opening a single modal locks page scroll
- [ ] Closing a single modal restores page scroll
- [ ] Opening two modals and closing the inner one keeps scroll locked
- [ ] Closing all modals restores scroll
- [ ] Rapid modal open/close does not leave scroll in wrong state
- [ ] Scroll event listeners continue to reposition popovers correctly
- [ ] Drag-and-drop on agents page works correctly
- [ ] Existing Vitest test suite passes with no regressions
