# Pipelines Page UI Consistency, Quality & UX Audit

**Date**: 2026-03-10  
**Scope**: `frontend/src/pages/AgentsPipelinePage.tsx` and its directly rendered pipeline components  
**Reviewer**: Copilot (`designer`)  
**Comparison baseline**: Shared catalog-page patterns from `AgentsPage`, `ProjectsPage`, `CelestialCatalogHero`, and `ProjectSelectionEmptyState`

## Executive Summary

- **Total findings**: 6
- **Critical**: 0
- **High**: 1
- **Medium**: 3
- **Low**: 2
- **Fixed in this PR**: 3 findings (`PIPE-001`, `PIPE-002`, `PIPE-003`)

The Pipelines page is broadly aligned with Solune’s celestial theme and shared catalog layout, but the audit found several change-scoped gaps around navigation continuity, long-text discoverability, and interaction safety. The highest-severity issue was a hero CTA that bypassed the page’s unsaved-changes safeguard, creating a data-loss risk and a mismatch with the empty-state pipeline creation flow.

## Surfaces Reviewed

- Page hero / primary actions
- Project selection empty state
- Loading state
- Pipeline editor toolbar
- Pipeline board and empty-board CTA
- Pipeline stages visualization
- Saved workflows list
- Recent activity cards
- Error messaging and unsaved-changes dialog

## Findings by Severity

| ID | Severity | Category | Status | Finding |
| --- | --- | --- | --- | --- |
| `PIPE-001` | High | Functional bug / UX | Fixed | The hero **New pipeline** CTA bypassed the unsaved-changes guard and did not reuse the same stage-prefill flow as the empty-state CTA. |
| `PIPE-002` | Medium | Functional bug / information architecture | Fixed | The hero **Saved workflows** anchor linked to `#saved-pipelines`, but the page had no matching target, so the shortcut did not move the user to the saved workflows section. |
| `PIPE-003` | Medium | UX / Visual quality | Fixed | Long pipeline names were visually truncated in **Saved Workflows** and **Recent Activity** with no way to inspect the full label. |
| `PIPE-004` | Medium | Accessibility | Open | Pipeline name validation feedback in `PipelineBoard` is only visual; the name input does not expose `aria-invalid` / `aria-describedby` for assistive technologies. |
| `PIPE-005` | Low | Visual consistency | Open | `SavedWorkflowsList` uses generic pulse blocks during loading, which feel flatter and less intentional than the app’s usual celestial panel skeletons. |
| `PIPE-006` | Low | UX clarity | Open | `Recent Activity` hard-caps to the three newest pipelines without an affordance or explanatory copy for seeing older activity. |

## Detailed Findings

### `PIPE-001` — Hero “New pipeline” bypassed unsaved-change protection

- **Severity**: High
- **Category**: Functional bug / UX
- **Affected files**: `frontend/src/pages/AgentsPipelinePage.tsx`
- **Reproduction steps**:
  1. Open an existing pipeline on the Pipelines page.
  2. Make a change so the editor becomes dirty.
  3. Click the hero-level **New pipeline** button.
- **Expected**: The page should reuse the guarded creation flow, prompting before discarding edits and preserving the board-column-derived stage setup.
- **Actual**: The hero CTA called `pipelineConfig.newPipeline()` directly instead of the page’s guarded `handleNewPipeline()` path.
- **Risk**: Users can lose unsaved work from the most visually prominent action on the page.
- **Remediation**: Route the hero CTA through `handleNewPipeline()` so both creation entry points behave consistently.
- **Status**: Fixed in this PR

### `PIPE-002` — Saved workflows jump link had no destination

- **Severity**: Medium
- **Category**: Functional bug / information architecture
- **Affected files**: `frontend/src/pages/AgentsPipelinePage.tsx`, `frontend/src/components/pipeline/SavedWorkflowsList.tsx`
- **Reproduction steps**:
  1. Open the Pipelines page.
  2. Click the hero-level **Saved workflows** button.
- **Expected**: Focus/scroll should jump to the saved workflows section.
- **Actual**: The hero link targeted `#saved-pipelines`, but the section lacked that anchor.
- **Remediation**: Add a named section wrapper with `id="saved-pipelines"` and an accessible heading relationship.
- **Status**: Fixed in this PR

### `PIPE-003` — Truncated pipeline names had no recovery path

- **Severity**: Medium
- **Category**: UX / visual quality
- **Affected files**: `frontend/src/components/pipeline/SavedWorkflowsList.tsx`, `frontend/src/pages/AgentsPipelinePage.tsx`
- **Expected**: Long pipeline names should remain discoverable without breaking the compact card layout.
- **Actual**: Names were truncated in cards and recent activity summaries with no tooltip or alternate reveal.
- **Remediation**: Preserve truncation for layout stability, but expose the full label via tooltip on hover/focus.
- **Status**: Fixed in this PR

### `PIPE-004` — Validation feedback is not fully announced to assistive tech

- **Severity**: Medium
- **Category**: Accessibility
- **Affected file**: `frontend/src/components/pipeline/PipelineBoard.tsx`
- **WCAG 2.1 mapping**:
  - **3.3.1 Error Identification**
  - **4.1.2 Name, Role, Value**
- **Observed issue**: The pipeline name field renders validation text, but the input does not expose `aria-invalid` or `aria-describedby` to bind the error text to the field.
- **Remediation**: Add an error ID, wire the input to that ID, and toggle `aria-invalid` when `validationErrors.name` is present.
- **Status**: Open

### `PIPE-005` — Loading skeletons are weaker than adjacent page patterns

- **Severity**: Low
- **Category**: Visual consistency
- **Affected file**: `frontend/src/components/pipeline/SavedWorkflowsList.tsx`
- **Observed issue**: The loading state uses plain pulse blocks instead of the richer rounded panel treatment used elsewhere in the Solune catalog.
- **Remediation**: Update the skeleton cards to better mirror the saved workflow card structure and panel styling.
- **Status**: Open

### `PIPE-006` — Recent activity limit is not explained

- **Severity**: Low
- **Category**: UX clarity
- **Affected file**: `frontend/src/pages/AgentsPipelinePage.tsx`
- **Observed issue**: The page always shows only three recent pipelines, but there is no hint that the list is intentionally abbreviated.
- **Remediation**: Add lightweight helper copy, a “View all workflows” affordance, or reuse the saved workflows section as the canonical destination.
- **Status**: Open

## Accessibility Notes

- **Keyboard access**: The major interactive surfaces reviewed from code remain keyboard reachable, including workflow cards and the empty-board creation CTA.
- **Focus visibility**: Existing focus rings on primary CTA controls are consistent with shared page patterns.
- **Outstanding gap**: `PIPE-004` remains the main assistive-technology issue found during this audit slice.

## Remediation Priority

1. **Address any remaining data-loss or state-consistency bugs first** — completed for `PIPE-001`.
2. **Remove broken wayfinding and text discoverability gaps** — completed for `PIPE-002` and `PIPE-003`.
3. **Finish the field-level accessibility pass in `PipelineBoard`** — recommended next.
4. **Polish lower-severity presentation gaps** — improve skeleton fidelity and recent-activity framing if additional iteration is available.

## Validation

- Targeted frontend tests for the updated Pipelines page surfaces
- Frontend lint
- Frontend type-check
- Frontend build
