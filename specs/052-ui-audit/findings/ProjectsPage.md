# Findings Report: ProjectsPage

**Page**: ProjectsPage.tsx | **Route**: /projects
**Audit Date**: 2026-03-18
**Auditor**: speckit.implement
**Line Count**: 629 (limit: 250) ⚠️ EXCEEDS by 2.5x
**Feature Dir**: src/components/board/
**Related Hooks**: useProjectBoard, useProjects, useBoardControls, useBoardRefresh, useRealTimeSync

## Summary

| Dimension | Passed | Failed | N/A | Total |
|-----------|--------|--------|-----|-------|
| Component Architecture | 2 | 5 | 0 | 7 |
| Data Fetching | 5 | 1 | 0 | 6 |
| Loading/Error/Empty States | 5 | 0 | 0 | 5 |
| Type Safety | 5 | 0 | 0 | 5 |
| Accessibility | 5 | 2 | 0 | 7 |
| Copy & UX Polish | 6 | 2 | 0 | 8 |
| Styling & Layout | 5 | 1 | 0 | 6 |
| Performance | 4 | 1 | 0 | 5 |
| Test Coverage | 4 | 1 | 0 | 5 |
| Code Hygiene | 5 | 1 | 0 | 6 |
| **Total** | **46** | **14** | **0** | **60** |

**Overall**: 46/60 items passing

## Findings

### Critical: ARCH-01 — Page exceeds 250-line limit (629 lines)

**Dimension**: Component Architecture
**Checklist Item**: ARCH-01 — Single Responsibility
**Location**: `src/pages/ProjectsPage.tsx:1-629`
**Related FR**: FR-020

**Issue**: ProjectsPage.tsx is 629 lines — 2.5× the limit. The page contains three large embedded sections: the pipeline stages visualization (lines 427–568), the pipeline assignment dropdown (lines 437–539), and the board section (lines 406–620).

**Remediation**:
1. Extract `PipelineStagesPanel` (pipeline stages + assignment dropdown) → `src/components/board/PipelineStagesPanel.tsx`
2. Extract `PipelineAssignmentDropdown` (the pipeline selector) → `src/components/board/PipelineAssignmentDropdown.tsx`
3. Move the rate limit effect + error computations to a `useProjectsPageRateLimit` hook or incorporate into existing hooks

**Verification**:
```bash
wc -l src/pages/ProjectsPage.tsx
# Expected: < 250
```

---

### Major: ARCH-06 — Complex inline rate-limit state derivation

**Dimension**: Component Architecture
**Checklist Item**: ARCH-06 — Hook extraction
**Location**: `src/pages/ProjectsPage.tsx:148-165`
**Related FR**: FR-023

**Issue**: Multiple lines of rate-limit state derivation (`projectsRateLimitError`, `boardRateLimitError`, `refreshRateLimitError`, etc.) are computed inline in the page component rather than encapsulated in a hook.

**Remediation**:
Extract rate-limit state derivation into the existing `useBoardRefresh` hook or a new `useProjectsRateLimit` hook.

---

### Major: ARCH-07 — Inline business logic in render

**Dimension**: Component Architecture
**Checklist Item**: ARCH-07 — No business logic in JSX
**Location**: `src/pages/ProjectsPage.tsx:357-366`
**Related FR**: FR-024

**Issue**: ApiError instanceof check and reason extraction inside JSX render tree (`{(() => { if (!(projectsError instanceof ApiError)) return null; ... })()}`).

**Remediation**:
Move error detail extraction to a computed variable above the return statement.

---

### Major: DATA-06 — assignPipelineMutation missing onError handler

**Dimension**: Data Fetching
**Checklist Item**: DATA-06 — Mutation error handling
**Location**: `src/pages/ProjectsPage.tsx:104-111`
**Related FR**: FR-005

**Issue**: `assignPipelineMutation` has `onSuccess` but no `onError` handler. If pipeline assignment fails, the user receives no feedback.

**Remediation**:
Add `onError` handler to `assignPipelineMutation` that shows a user-visible error message.

---

### Minor: A11Y-03 — Pipeline assignment dropdown missing ARIA listbox role

**Dimension**: Accessibility
**Checklist Item**: A11Y-03 — ARIA attributes
**Location**: `src/pages/ProjectsPage.tsx:437-539`
**Related FR**: FR-010

**Issue**: The pipeline assignment dropdown uses a custom `div`-based popup without a proper `role="listbox"` on the container or `role="option"` on items. The trigger button has `aria-haspopup="listbox"` and `aria-expanded`, which is good, but the dropdown list itself needs proper ARIA roles.

**Remediation**:
Add `role="listbox"` to the dropdown container and `role="option"` + `aria-selected` to each pipeline item.

---

### Minor: COPY-05 — assignPipelineMutation missing success feedback

**Dimension**: Copy & UX Polish
**Checklist Item**: COPY-05 — Success feedback
**Location**: `src/pages/ProjectsPage.tsx:104-111`
**Related FR**: FR-017

**Issue**: Pipeline assignment mutation closes the dropdown on success but shows no user-visible feedback (no toast, no status message).

**Remediation**:
Add a brief success message or toast on pipeline assignment success.

---

### Minor: PERF-01 — Pipeline stages section re-renders on any board data change

**Dimension**: Performance
**Checklist Item**: PERF-01 — No unnecessary re-renders
**Location**: `src/pages/ProjectsPage.tsx:427-568`
**Related FR**: —

**Issue**: Pipeline stages visualization is inline in the page without memoization, causing re-renders on any board update.

**Remediation**:
After extraction to `PipelineStagesPanel`, wrap with `React.memo` if props are stable.

---

## Remediation Plan

### Phase 1: Structural Fixes
- [ ] ARCH-01 — Extract PipelineStagesPanel → `src/components/board/PipelineStagesPanel.tsx`
- [ ] ARCH-01 — Extract PipelineAssignmentDropdown → `src/components/board/PipelineAssignmentDropdown.tsx`
- [ ] ARCH-06 — Extract rate-limit state to hook
- [ ] ARCH-07 — Move ApiError extraction out of JSX

### Phase 2: States & Error Handling
- [ ] DATA-06 — Add onError to assignPipelineMutation
- [ ] COPY-05 — Add success feedback on pipeline assignment

### Phase 3: Accessibility & UX
- [ ] A11Y-03 — Add role="listbox" and role="option" to pipeline dropdown

### Phase 4: Testing
- [ ] TEST-04 — Add rate limit error test case

### Phase 5: Validation
- [ ] ESLint: 0 warnings
- [ ] TypeScript: 0 errors
- [ ] Tests: all pass
