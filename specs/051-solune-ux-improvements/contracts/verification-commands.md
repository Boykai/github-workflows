# Verification Commands: Solune UX Improvements

**Feature Branch**: `051-solune-ux-improvements`
**Date**: 2026-03-19
**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

## Automated Verification

### Type Check

```bash
cd solune/frontend
npx tsc --noEmit
```

**Expected**: Exit code 0, no type errors.

### Lint

```bash
cd solune/frontend
npx eslint .
```

**Expected**: Exit code 0, no lint warnings or errors.

### Unit Tests

```bash
cd solune/frontend
npx vitest run
```

**Expected**: All tests pass. Coverage thresholds met (statements: 50%, branches: 44%, functions: 41%, lines: 50%).

### Unit Tests (Specific Files)

```bash
# Test responsive hook
npx vitest run src/hooks/useMediaQuery.test.ts

# Test modified components
npx vitest run src/components/chat/ChatPopup.test.tsx
npx vitest run src/components/board/IssueDetailModal.test.tsx
npx vitest run src/components/board/BoardToolbar.test.tsx
npx vitest run src/components/common/EmptyState.test.tsx

# Test modified hooks
npx vitest run src/hooks/useBoardDragDrop.test.ts
npx vitest run src/hooks/useApps.test.ts
npx vitest run src/hooks/usePipelineConfig.test.ts
npx vitest run src/hooks/useOnboarding.test.tsx

# Test modified pages
npx vitest run src/pages/AgentsPage.test.tsx
npx vitest run src/pages/ToolsPage.test.tsx
npx vitest run src/pages/ChoresPage.test.tsx
npx vitest run src/pages/AppsPage.test.tsx
```

### E2E Tests

```bash
cd solune/frontend
npx playwright test
```

**Expected**: All E2E specs pass (10 spec files).

### Build

```bash
cd solune/frontend
npm run build
```

**Expected**: Exit code 0, successful production build.

## Manual Verification

### Responsive Testing

Test at the following viewport widths using Chrome DevTools Device Toolbar:

| Viewport | Device Emulation | Test Areas |
|----------|-----------------|------------|
| 320px | iPhone SE | Chat bottom-sheet, sidebar collapse, modal full-screen |
| 375px | iPhone 12/13 | All mobile behaviors |
| 768px | iPad (portrait) | Breakpoint transition — should be desktop layout |
| 1024px | iPad (landscape) | Standard desktop layout |

**Checklist per viewport**:
- [ ] Chat opens correctly (bottom-sheet on mobile, floating on desktop)
- [ ] Sidebar auto-collapses on mobile, overlay when expanded
- [ ] Issue modal is full-screen on mobile, centered dialog on desktop
- [ ] Board toolbar is compact on mobile, full row on desktop
- [ ] No horizontal scrolling at any viewport width

### Perceived Performance Testing

```
Chrome DevTools → Network tab → Throttle to "Slow 3G"
```

- [ ] Navigate to Agents page → skeleton loaders visible during load
- [ ] Navigate to Tools page → skeleton loaders visible during load
- [ ] Navigate to Chores page → skeleton loaders visible during load
- [ ] Navigate to Apps page → skeleton loaders visible during load
- [ ] Skeletons transition to content without layout shift
- [ ] Drag an issue card → card moves instantly despite network delay
- [ ] Start/stop an app → status updates instantly despite network delay

### Toast Notification Testing

- [ ] Create an agent → success toast appears and auto-dismisses
- [ ] Delete a tool → success toast appears and auto-dismisses
- [ ] Trigger a server error → error toast appears and persists until dismissed
- [ ] Perform rapid operations → toasts stack without overlapping

### Empty State Testing

- [ ] Select a project with no agents → "Create your first agent" empty state shown
- [ ] Select a project with no tools → "Create your first tool" empty state shown
- [ ] Select a project with no chores → "Create your first chore" empty state shown
- [ ] Click CTA button → create dialog opens
- [ ] Create first item → empty state replaced by item list

### Search Testing

- [ ] Type in board search → only matching issues shown
- [ ] Clear search → all issues restored
- [ ] Search with no matches → "No results found" message
- [ ] Type in catalog page search → matching items filtered
- [ ] Search responds within 300ms for datasets up to 500 items

### Onboarding Tour Testing

- [ ] Trigger onboarding tour → all 13 steps display correctly
- [ ] New steps (Tools, Chores, Settings, Apps) highlight correct sidebar items
- [ ] Skip button works at any step → tour marked complete
- [ ] Complete full tour → tour doesn't appear on next visit
- [ ] Tour tooltips are positioned correctly and don't overflow viewport

### Undo/Redo Testing

- [ ] Make pipeline change → Ctrl+Z undoes change
- [ ] After undo → Ctrl+Shift+Z redoes change
- [ ] Multiple undos → each reverts one step
- [ ] New change after undo → redo stack cleared
- [ ] Load pipeline from server → undo/redo stacks cleared
- [ ] Discard pipeline → undo/redo stacks cleared

### Keyboard Accessibility

- [ ] Tab to board → Space to pick up card → Arrow keys to move → Space to drop
- [ ] Tab through all interactive elements at 375px viewport
- [ ] Escape closes modals, sidebar overlay, and chat bottom-sheet
- [ ] Focus indicators visible on all interactive elements
