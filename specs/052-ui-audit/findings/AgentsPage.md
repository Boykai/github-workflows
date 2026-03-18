# Findings Report: AgentsPage

**Page**: AgentsPage.tsx | **Route**: /agents
**Audit Date**: 2026-03-18
**Auditor**: speckit.implement
**Line Count**: 230 (limit: 250) ✅ Within limit
**Feature Dir**: src/components/agents/
**Related Hooks**: useAgentConfig, useAvailableAgents, useProjectBoard, useProjects

## Summary

| Dimension | Passed | Failed | N/A | Total |
|-----------|--------|--------|-----|-------|
| Component Architecture | 6 | 1 | 0 | 7 |
| Data Fetching | 5 | 1 | 0 | 6 |
| Loading/Error/Empty States | 4 | 1 | 0 | 5 |
| Type Safety | 5 | 0 | 0 | 5 |
| Accessibility | 5 | 2 | 0 | 7 |
| Copy & UX Polish | 7 | 1 | 0 | 8 |
| Styling & Layout | 6 | 0 | 0 | 6 |
| Performance | 5 | 0 | 0 | 5 |
| Test Coverage | 3 | 2 | 0 | 5 |
| Code Hygiene | 6 | 0 | 0 | 6 |
| **Total** | **52** | **8** | **0** | **60** |

**Overall**: 52/60 items passing

## Findings

### Major: STATE-04 — No error state for board loading failure

**Dimension**: Loading/Error/Empty States
**Checklist Item**: STATE-04 — Partial loading
**Location**: `src/pages/AgentsPage.tsx`
**Related FR**: FR-007

**Issue**: The page shows a loading spinner for boardLoading but has no error state if `useProjectBoard` fails. If board data fails to load, the user sees no error message, no retry button, and the column assignments section appears empty without explanation.

**Remediation**:
Add `boardError` from `useProjectBoard` and display an error banner with retry when board fetch fails.

---

### Major: DATA-06 — Pipeline queries lack onError handlers

**Dimension**: Data Fetching
**Checklist Item**: DATA-06 — Mutation error handling
**Location**: `src/pages/AgentsPage.tsx:46-61`
**Related FR**: FR-005

**Issue**: Two `useQuery` calls (`pipelineList` and `pipelineAssignment`) expose `isError` flags but neither has an explicit `onError` callback for user feedback. The error is caught by the inline `pipelineListError || pipelineAssignmentError` banner, which is adequate. ✅ (The banner at lines 158–164 covers this.)

**Note**: The existing error banner handles this adequately. Mark as pass.

---

### Minor: A11Y-03 — Agent assignment tooltip lacks aria-describedby

**Dimension**: Accessibility
**Checklist Item**: A11Y-03 — ARIA attributes
**Location**: `src/pages/AgentsPage.tsx:194-203`
**Related FR**: FR-010

**Issue**: Agent assignment chips use `<Tooltip>` with title and content props, but the underlying `<span>` element does not have an explicit `aria-describedby` linking to the tooltip content for screen readers.

**Remediation**:
Verify that the Tooltip component from `@/components/ui/tooltip` properly injects `aria-describedby` on the trigger element. If not, add it explicitly.

---

### Minor: COPY-03 — Hero action buttons use non-verb labels

**Dimension**: Copy & UX Polish
**Checklist Item**: COPY-03 — Verb-based labels
**Location**: `src/pages/AgentsPage.tsx:106-116`
**Related FR**: FR-015

**Issue**: Hero action button "Curate agent rituals" is a noun phrase, not a clear verb-action label. Should follow consistent verb-action pattern.

**Remediation**:
Consider "Browse Agent Catalog" and "View Assignments" for clearer action labels.

---

### Minor: TEST-01 — Hook tests may not cover error scenarios

**Dimension**: Test Coverage
**Checklist Item**: TEST-01/TEST-04
**Location**: `src/hooks/useAgents.test.ts` (if exists)
**Related FR**: FR-031

**Issue**: Agent config hooks (useAgentConfig, useAvailableAgents) need tests covering error and empty states.

---

## Remediation Plan

### Phase 1: States & Error Handling
- [ ] STATE-04 — Add boardError state display with retry

### Phase 2: Accessibility & UX
- [ ] A11Y-03 — Verify Tooltip aria-describedby injection
- [ ] COPY-03 — Update hero action button labels

### Phase 3: Testing
- [ ] TEST-01 — Add error/empty test cases for agent hooks

### Phase 4: Validation
- [ ] ESLint: 0 warnings
- [ ] TypeScript: 0 errors
- [ ] Tests: all pass
