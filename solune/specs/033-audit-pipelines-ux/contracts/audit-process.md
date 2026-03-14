# Audit Process Contracts: Pipelines Page UI Audit

**Feature**: 033-audit-pipelines-ux | **Date**: 2026-03-10

## Audit Scope

### In-Scope Components

Every UI element rendered by `AgentsPipelinePage.tsx` and its child component tree:

| Component | File | Lines | Audit Categories |
|-----------|------|-------|-----------------|
| **AgentsPipelinePage** | `pages/AgentsPipelinePage.tsx` | ~460 | All 5 categories |
| **PipelineBoard** | `components/pipeline/PipelineBoard.tsx` | ~312 | Visual, Functional, A11y, Code |
| **StageCard** | `components/pipeline/StageCard.tsx` | ~363 | Visual, Functional, A11y, Code |
| **AgentNode** | `components/pipeline/AgentNode.tsx` | ~123 | Visual, A11y, Code |
| **PipelineToolbar** | `components/pipeline/PipelineToolbar.tsx` | ~173 | Visual, Functional, UX, Code |
| **SavedWorkflowsList** | `components/pipeline/SavedWorkflowsList.tsx` | ~220 | Visual, Functional, A11y, UX, Code |
| **PipelineFlowGraph** | `components/pipeline/PipelineFlowGraph.tsx` | ~230 | Visual, A11y, Code |
| **ModelSelector** | `components/pipeline/ModelSelector.tsx` | ~300 | Visual, A11y, UX |
| **PipelineModelDropdown** | `components/pipeline/PipelineModelDropdown.tsx` | ~110 | Visual, A11y |
| **UnsavedChangesDialog** | `components/pipeline/UnsavedChangesDialog.tsx` | ~70 | Functional, A11y, UX |
| **PresetBadge** | `components/pipeline/PresetBadge.tsx` | ~30 | Visual |

### Out of Scope

- Application-level shared components (navigation, theme provider) — audited only in context of Pipelines page appearance
- Backend API endpoints — referenced for data model understanding only
- Other pages — used as comparison baseline, not audited themselves
- Performance profiling (e.g., React Profiler, Lighthouse performance score) — spec focuses on functional quality

---

## Audit Category Contracts

### Category 1: Visual Consistency (User Story 1 — P1)

**Input**: Design tokens from `index.css`, visual patterns from AgentsPage/ProjectsPage/Dashboard

**Process**:

1. For each component in scope, extract all visual properties used:
   - Colors (background, text, border, shadow)
   - Typography (font family, size, weight, line height)
   - Spacing (padding, margin, gap)
   - Border treatment (radius, width, opacity)
   - Animation/transition timing

2. Compare extracted properties against design tokens:
   - Colors MUST use CSS custom properties (`var(--primary)`, etc.) or Tailwind semantic classes
   - Typography MUST use `font-display` or `font-sans` token
   - Border radius MUST use `--radius-sm/md/lg` or Tailwind `rounded-*` mapped to tokens
   - Animations MUST use `--transition-cosmic-*` or `--animate-*` tokens

3. Compare Pipelines page patterns against equivalent elements on other pages:
   - Buttons: Same variant classes as AgentsPage/ProjectsPage?
   - Cards: Same `celestial-panel` or card pattern?
   - Loading states: Same `CelestialLoader` pattern?
   - Empty states: Same dashed-border message pattern?
   - Section headings: Same typography hierarchy?

**Output**: Finding per deviation with expected token vs actual value

**Acceptance**: FR-001, FR-002 satisfied — every component reviewed, cross-page comparison with ≥3 pages

---

### Category 2: Functional Bug & Edge Case Audit (User Story 2 — P1)

**Input**: Interactive elements on Pipelines page, state machine from `usePipelineConfig`

**Process**:

1. Exercise every interactive element across all states:

   | Element | States to Test |
   |---------|---------------|
   | New Pipeline button | Empty board, dirty board, clean board |
   | Save button | Creating, editing (dirty/clean), preset |
   | Delete button | Editing (non-preset), preset (should be hidden) |
   | Discard button | Creating (dirty/clean), editing (dirty/clean) |
   | Pipeline name input | Valid, empty, whitespace, max length, special chars |
   | Stage name input | Valid, empty, duplicate, max length |
   | Agent drag-and-drop | Reorder within stage, single agent, many agents |
   | Model selector | Select model, change model, "Auto" option |
   | Saved workflow cards | Click to load, keyboard Enter/Space, assign button |
   | Unsaved changes dialog | Save, Discard, Cancel, Escape, backdrop click |

2. Verify all UI states:

   | State | Expected Behavior |
   |-------|------------------|
   | No project selected | `ProjectSelectionEmptyState` with guidance |
   | Loading board data | `CelestialLoader` with label, no layout shift |
   | Empty board (no pipeline) | CTA to create first pipeline, clear guidance |
   | Creating pipeline | Editable board with save/discard toolbar |
   | Editing pipeline | Full toolbar with save/delete/discard |
   | Save error | Error banner with clear message, form state preserved |
   | Network error | Actionable error message |

3. Check console for errors/warnings in development mode

**Output**: Finding per bug with reproduction steps, expected vs actual behavior

**Acceptance**: FR-003, FR-004, FR-009 satisfied — all interactions tested, all states verified, console checked

---

### Category 3: Accessibility Compliance (User Story 3 — P2)

**Input**: WCAG 2.1 Level AA success criteria, keyboard navigation paths, screen reader output

**Process**:

1. Keyboard navigation audit:
   - Tab through all interactive elements — verify each is reachable
   - Enter/Space activation for buttons and links
   - Escape to close dialogs and cancel edits
   - Arrow keys for drag-and-drop (via `KeyboardSensor`)
   - Focus indicators visible on all focusable elements

2. Screen reader audit:
   - All images and icons have appropriate `alt` or `aria-label`
   - Dynamic content changes announced via live regions or focus management
   - Form inputs have associated labels
   - Validation errors linked to inputs via `aria-describedby`
   - Dialog focus management (trap focus, return focus on close)

3. Color contrast audit:
   - All text meets 4.5:1 ratio (normal text) or 3:1 (large text)
   - Interactive elements distinguishable by more than color alone
   - Focus indicators meet 3:1 contrast against adjacent colors

4. ARIA compliance:
   - `role` attributes appropriate and not redundant
   - `aria-expanded`, `aria-selected`, `aria-invalid` used correctly
   - `aria-live` regions for dynamic announcements

**WCAG 2.1 Success Criteria Checklist**:

| SC | Title | Relevant Element |
|----|-------|-----------------|
| 1.1.1 | Non-text Content | Icons, flow graph SVG |
| 1.3.1 | Info and Relationships | Form labels, section headings, error-input association |
| 1.4.3 | Contrast (Minimum) | All text, interactive elements |
| 1.4.11 | Non-text Contrast | Focus indicators, form borders |
| 2.1.1 | Keyboard | All interactive elements |
| 2.4.3 | Focus Order | Tab order through pipeline board |
| 2.4.7 | Focus Visible | Focus indicators on all elements |
| 3.3.1 | Error Identification | Pipeline name validation (PIPE-004) |
| 3.3.2 | Labels or Instructions | Form inputs, model selector |
| 4.1.2 | Name, Role, Value | All interactive components |

**Output**: Finding per violation mapped to specific WCAG SC

**Acceptance**: FR-005, FR-006, FR-007 satisfied — keyboard, contrast, and AT announcements verified

---

### Category 4: UX Quality & Information Architecture (User Story 4 — P2)

**Input**: Page layout, interaction patterns, user task flows

**Process**:

1. Information hierarchy assessment:
   - Is the page purpose immediately clear?
   - Are primary actions (New Pipeline, Save) visually prominent?
   - Is the relationship between sections (board, saved workflows, activity) logical?

2. Responsiveness audit:
   - Test at standard breakpoints: 768px (tablet), 1024px (desktop), 1440px (wide)
   - Verify no overflow or inaccessible elements at any breakpoint
   - Check that grid layouts adapt appropriately

3. Interaction feedback:
   - All actions produce visible feedback (save → success/error, delete → confirmation)
   - Loading states shown during async operations
   - Transitions use appropriate cosmic timing tokens

4. Terminology consistency:
   - Compare labels and terms with other pages
   - "Pipeline" vs "Workflow" usage
   - Button labels match actions

**Output**: Finding per UX issue with severity and improvement recommendation

**Acceptance**: FR-008, FR-011 satisfied — responsiveness tested, remediation recommendations provided

---

### Category 5: Code Quality & Best Practices (User Story 5 — P3)

**Input**: Source code of all pipeline components, project conventions

**Process**:

1. Class name composition:
   - All `className` values use `cn()` from `@/lib/utils`
   - No template literal classNames (enforced by convention)

2. Shared pattern reuse:
   - Loading states use `CelestialLoader` or consistent skeleton pattern
   - Empty states follow dashed-border pattern from other pages
   - Error handling follows existing patterns

3. Component architecture:
   - Separation of concerns (presentation vs logic)
   - Hook usage follows TanStack Query patterns
   - No unnecessary re-renders from missing memoization

4. Console cleanliness:
   - No unexpected warnings or errors
   - No deprecated API usage
   - No missing key props in lists

5. TypeScript compliance:
   - `noUnusedLocals: true` and `noUnusedParameters: true` enforced
   - No `any` types where avoidable
   - Proper null checking

**Output**: Finding per code quality issue with file/line reference and fix recommendation

**Acceptance**: FR-009, FR-011 satisfied — console clean, recommendations provided
