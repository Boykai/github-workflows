# Findings Report Template

**Feature**: 052-ui-audit | **Version**: 1.0 | **Date**: 2026-03-18

## Purpose

Template for per-page audit findings reports. Each page audit produces one findings report following this structure. The report documents the evaluation of all 60 checklist items and provides actionable remediation guidance for failing items.

---

## Report Structure

### Header

```markdown
# Findings Report: [PageName]

**Page**: [PageName].tsx | **Route**: [/route-path]
**Audit Date**: [YYYY-MM-DD]
**Auditor**: [agent or person]
**Line Count**: [N] (limit: 250)
**Feature Dir**: src/components/[feature]/
**Related Hooks**: [list of hooks]
```

### Summary Scorecard

```markdown
## Summary

| Dimension | Passed | Failed | N/A | Total |
|-----------|--------|--------|-----|-------|
| Component Architecture | X | Y | Z | 7 |
| Data Fetching | X | Y | Z | 6 |
| Loading/Error/Empty States | X | Y | Z | 5 |
| Type Safety | X | Y | Z | 5 |
| Accessibility | X | Y | Z | 7 |
| Copy & UX Polish | X | Y | Z | 8 |
| Styling & Layout | X | Y | Z | 6 |
| Performance | X | Y | Z | 5 |
| Test Coverage | X | Y | Z | 5 |
| Code Hygiene | X | Y | Z | 6 |
| **Total** | **X** | **Y** | **Z** | **60** |

**Overall**: X/60 items passing
```

### Detailed Findings

```markdown
## Findings

### [SEVERITY]: [Checklist Item ID] — [Short Description]

**Dimension**: [Dimension Name]
**Checklist Item**: [Full checklist item text]
**Location**: `src/pages/[Page].tsx:L[start]-L[end]`
**Related FR**: [FR-NNN]

**Issue**: [Specific description of what was found]

**Remediation**:
[Step-by-step fix instructions]

**Verification**:
[Command or test to verify the fix]

---
```

### Remediation Plan

```markdown
## Remediation Plan

### Phase 1: Structural Fixes
- [ ] [Finding ID] — [Short description]
- [ ] [Finding ID] — [Short description]

### Phase 2: States & Error Handling
- [ ] [Finding ID] — [Short description]

### Phase 3: Accessibility & UX
- [ ] [Finding ID] — [Short description]

### Phase 4: Testing
- [ ] [Finding ID] — [Short description]

### Phase 5: Validation
- [ ] ESLint: 0 warnings
- [ ] TypeScript: 0 errors
- [ ] Tests: all pass
- [ ] Visual: light mode, dark mode, 768px–1920px
```

---

## Severity Definitions

| Severity | Description | Examples | Fix Priority |
|----------|-------------|----------|-------------|
| **Critical** | User-facing bug or accessibility blocker | Blank screen during load, keyboard-inaccessible button, unguarded delete action | Must fix — blocks audit completion |
| **Major** | Quality gap degrading UX or maintainability | Missing error state, page exceeds 250 lines, `any` type usage | Should fix — required for quality bar |
| **Minor** | Polish item improving consistency | Missing tooltip on truncated text, inconsistent spacing, copy inconsistency | Nice to fix — improves polish |

## Output Location

Findings reports are stored in the feature's specs directory during task execution:

```
specs/052-ui-audit/
└── findings/
    ├── AppsPage.md
    ├── ProjectsPage.md
    ├── AgentsPipelinePage.md
    └── ...
```

**Note**: The `findings/` directory is created during task implementation (Phase 4: Implement), not during planning. This template defines the expected output format.
