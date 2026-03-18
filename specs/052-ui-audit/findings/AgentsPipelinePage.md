# Findings Report: AgentsPipelinePage

**Page**: AgentsPipelinePage.tsx | **Route**: /pipeline
**Audit Date**: 2026-03-18
**Auditor**: speckit.implement
**Line Count**: 417 (limit: 250) ⚠️ EXCEEDS by 1.7x
**Feature Dir**: src/components/pipeline/
**Related Hooks**: usePipelineConfig, usePipelineReducer, useProjectBoard, useAgentConfig, useAvailableAgents

## Summary

| Dimension | Passed | Failed | N/A | Total |
|-----------|--------|--------|-----|-------|
| Component Architecture | 3 | 4 | 0 | 7 |
| Data Fetching | 6 | 0 | 0 | 6 |
| Loading/Error/Empty States | 5 | 0 | 0 | 5 |
| Type Safety | 5 | 0 | 0 | 5 |
| Accessibility | 5 | 2 | 0 | 7 |
| Copy & UX Polish | 7 | 1 | 0 | 8 |
| Styling & Layout | 4 | 2 | 0 | 6 |
| Performance | 5 | 0 | 0 | 5 |
| Test Coverage | 4 | 1 | 0 | 5 |
| Code Hygiene | 4 | 2 | 0 | 6 |
| **Total** | **48** | **12** | **0** | **60** |

**Overall**: 48/60 items passing

## Findings

### Critical: ARCH-01 — Page exceeds 250-line limit (417 lines)

**Dimension**: Component Architecture
**Checklist Item**: ARCH-01 — Single Responsibility
**Location**: `src/pages/AgentsPipelinePage.tsx:1-417`
**Related FR**: FR-020

**Issue**: AgentsPipelinePage.tsx is 417 lines. The pipeline stages visualization section (lines 348–395) is an inline section that renders board columns with agent assignments — this is a self-contained visualization panel.

**Remediation**:
1. Extract the pipeline stages visualization (lines 348–395) into `src/components/pipeline/PipelineStagesVisualization.tsx`
2. The unsaved dialog state management (lines 92–98) + handlers (lines 100–172) could be extracted into a `useUnsavedPipelineDialog` hook

**Verification**:
```bash
wc -l src/pages/AgentsPipelinePage.tsx
# Expected: < 250
```

---

### Major: ARCH-06 — Unsaved dialog state management inline

**Dimension**: Component Architecture
**Checklist Item**: ARCH-06 — Hook extraction
**Location**: `src/pages/AgentsPipelinePage.tsx:92-172`
**Related FR**: FR-023

**Issue**: The unsaved changes dialog state (`unsavedDialog`) and its handlers (handleUnsavedSave, handleUnsavedDiscard, handleUnsavedCancel, handleWorkflowSelect, handleWorkflowCopy, handleNewPipeline) account for ~80 lines of state management that could be encapsulated in a hook.

**Remediation**:
Extract unsaved dialog state and handlers into `useUnsavedPipelineDialog` hook.

---

### Major: HYGIENE-02 — console.warn in production code

**Dimension**: Code Hygiene
**Checklist Item**: HYGIENE-02 — No console.log
**Location**: `src/pages/AgentsPipelinePage.tsx:83`
**Related FR**: FR-030

**Issue**: `console.warn('Failed to seed preset pipelines:', err)` should use proper error handling or be removed.

**Remediation**:
Remove `console.warn` — the catch block can be silent (seeding is best-effort and idempotent) or use a logger utility.

---

### Minor: A11Y-05 — Status color dots without text/icon alternative

**Dimension**: Accessibility
**Checklist Item**: A11Y-05 — Color contrast
**Location**: `src/pages/AgentsPipelinePage.tsx:366`
**Related FR**: FR-012

**Issue**: Status color dots in pipeline stages (`style={{ backgroundColor: dotColor }}`) convey column status via color only, without text or icon alternative for colorblind users.

**Remediation**:
Add `aria-label` to the color dot span with the status name, e.g. `aria-label={col.status.name}`.

---

### Minor: STYLE-01 — Inline style for dynamic grid and dot colors

**Dimension**: Styling & Layout
**Checklist Item**: STYLE-01 — Tailwind only
**Location**: `src/pages/AgentsPipelinePage.tsx:62, 366`
**Related FR**: —

**Issue**: `alignedGridStyle` uses `style={{ gridTemplateColumns: ... }}` (acceptable for truly dynamic grid) and dot color uses `style={{ backgroundColor: dotColor }}` (dynamic CSS color value). These cannot be replaced with static Tailwind classes since the values are runtime-computed.

**Note**: This is an acceptable use of inline styles for truly dynamic values. Mark as N/A.

---

### Minor: COPY-03 — "New pipeline" button uses lowercase

**Dimension**: Copy & UX Polish
**Checklist Item**: COPY-03 — Verb-based action labels
**Location**: `src/pages/AgentsPipelinePage.tsx:230`
**Related FR**: FR-015

**Issue**: Hero action button label "New pipeline" should be "Create Pipeline" for consistent verb-based labeling.

**Remediation**:
Change "New pipeline" to "Create Pipeline".

---

### Minor: HYGIENE-03 — All imports correctly use @/ alias ✅

**Dimension**: Code Hygiene
**Checklist Item**: HYGIENE-03 — @/ import alias
**Location**: `src/pages/AgentsPipelinePage.tsx:1-35`

**Issue**: No relative imports found. All imports use `@/` alias. This is a pass. ✅

---

## Remediation Plan

### Phase 1: Structural Fixes
- [ ] ARCH-01 — Extract PipelineStagesVisualization → `src/components/pipeline/PipelineStagesVisualization.tsx`
- [ ] ARCH-06 — Extract useUnsavedPipelineDialog hook (optional — improves clarity)
- [ ] HYGIENE-02 — Remove console.warn from preset seeding

### Phase 2: States & Error Handling
- [ ] ✅ All loading/error/empty states properly handled

### Phase 3: Accessibility & UX
- [ ] A11Y-05 — Add aria-label to status color dots
- [ ] COPY-03 — Change "New pipeline" to "Create Pipeline"

### Phase 4: Testing
- [ ] TEST-04 — Add pipeline error state test coverage

### Phase 5: Validation
- [ ] ESLint: 0 warnings
- [ ] TypeScript: 0 errors
- [ ] Tests: all pass
