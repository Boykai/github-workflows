# Findings Report: ChoresPage

**Page**: ChoresPage.tsx | **Route**: /chores
**Audit Date**: 2026-03-18
**Auditor**: speckit.implement
**Line Count**: 166 (limit: 250) ✅ Within limit
**Feature Dir**: src/components/chores/
**Related Hooks**: useChoresList, useEvaluateChoresTriggers, useProjectBoard, useUnsavedChanges

## Summary

| Dimension | Passed | Failed | N/A | Total |
|-----------|--------|--------|-----|-------|
| Component Architecture | 6 | 1 | 0 | 7 |
| Data Fetching | 5 | 1 | 0 | 6 |
| Loading/Error/Empty States | 4 | 1 | 0 | 5 |
| Type Safety | 5 | 0 | 0 | 5 |
| Accessibility | 6 | 1 | 0 | 7 |
| Copy & UX Polish | 7 | 1 | 0 | 8 |
| Styling & Layout | 5 | 1 | 0 | 6 |
| Performance | 5 | 0 | 0 | 5 |
| Test Coverage | 3 | 2 | 0 | 5 |
| Code Hygiene | 5 | 1 | 0 | 6 |
| **Total** | **51** | **9** | **0** | **60** |

**Overall**: 51/60 items passing

## Findings

### Major: HYGIENE-02 — console.warn in production code

**Dimension**: Code Hygiene
**Checklist Item**: HYGIENE-02 — No console.log
**Location**: `src/pages/ChoresPage.tsx:45`
**Related FR**: FR-030

**Issue**: `console.warn('Failed to seed preset chores:', err)` in the chore preset seeding `useEffect`. This should be removed or replaced with silent failure since seeding is idempotent.

**Remediation**:
Remove the `console.warn` statement. The catch block can remain empty (seeding is best-effort).

---

### Major: STATE-01 — No loading state for chore list

**Dimension**: Loading/Error/Empty States
**Checklist Item**: STATE-01 — Loading state
**Location**: `src/pages/ChoresPage.tsx`
**Related FR**: FR-004

**Issue**: `useChoresList` is destructured as `{ data: chores }` without capturing `isLoading` or `error`. If the chore list is loading, no indicator is shown — the `FeaturedRitualsPanel` and `ChoresPanel` receive `undefined` data without any loading feedback.

**Remediation**:
Destructure `isLoading` and `error` from `useChoresList`. Show `<CelestialLoader>` while loading and an error banner with retry if the fetch fails.

---

### Major: ARCH-07 — Unsaved changes modal is inline UI logic

**Dimension**: Component Architecture
**Checklist Item**: ARCH-07 — No business logic in JSX
**Location**: `src/pages/ChoresPage.tsx:136-162`
**Related FR**: FR-024

**Issue**: The unsaved changes confirmation modal is implemented as raw JSX inline in the page (a custom modal using fixed positioning and Button components) rather than using the shared `<ConfirmationDialog>` component from `@/components/ui/confirmation-dialog`.

**Remediation**:
Replace the custom unsaved changes modal with the `ConfirmationDialog` component or `useConfirmation` hook pattern.

---

### Minor: A11Y-05 — Unsaved changes modal backdrop missing aria-hidden

**Dimension**: Accessibility
**Checklist Item**: A11Y-05 — Focus management
**Location**: `src/pages/ChoresPage.tsx:140`
**Related FR**: FR-009

**Issue**: The unsaved changes modal backdrop div uses `role="presentation"` but lacks `aria-hidden="true"`. Background content may be accessible to screen readers when the modal is open.

**Remediation**:
Add `aria-hidden="true"` to the backdrop. Use `ConfirmationDialog` which handles focus trapping correctly.

---

### Minor: DATA-06 — workflowApi query missing error handling

**Dimension**: Data Fetching
**Checklist Item**: DATA-06 — Mutation error handling
**Location**: `src/pages/ChoresPage.tsx:62-70`
**Related FR**: FR-005

**Issue**: The `workflowApi.getConfig()` query has no error handling displayed to the user. If it fails, the repo info is silently unavailable (hero shows "Awaiting repository" which is acceptable) but there's no indication of an error.

**Remediation**:
This is a non-critical, silent fallback. The behavior is acceptable — mark as minor. No immediate fix required.

---

## Remediation Plan

### Phase 1: States & Error Handling
- [ ] STATE-01 — Add loading/error states for useChoresList

### Phase 2: Structural
- [ ] ARCH-07 — Replace custom unsaved modal with ConfirmationDialog

### Phase 3: Accessibility
- [ ] A11Y-05 — Fix modal backdrop aria-hidden

### Phase 4: Code Hygiene
- [ ] HYGIENE-02 — Remove console.warn from preset seeding

### Phase 5: Validation
- [ ] ESLint: 0 warnings
- [ ] TypeScript: 0 errors
- [ ] Tests: all pass
