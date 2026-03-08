---
name: Accessibility Check
about: Recurring chore for a custom GitHub agent to analyze and improve accessibility across the codebase
title: '[CHORE] Accessibility Check'
labels: chore
assignees: ''
---

## Accessibility Check

Use a custom GitHub coding agent to perform a deep accessibility review across the live #codebase, then apply the highest-value safe accessibility fixes directly in code.

This repository is actively evolving. Do not assume the stack, frameworks, languages, package managers, rendering model, component library, or dependency set are static. Start by discovering the current implementation and accessibility surface from the repository as it exists today, then adapt the review plan to what is actually present.

## Agent Objective

Produce a practical accessibility pass that:

1. Discovers the current stack, UI surfaces, navigation patterns, forms, dialogs, interactive controls, content structures, and rendering paths.
2. Identifies real accessibility gaps, semantic issues, keyboard traps, focus-management problems, screen-reader issues, contrast risks, motion concerns, and missing states or labels.
3. Applies low-risk and medium-risk accessibility fixes directly where the correct remediation is clear.
4. Adds or updates tests, validation, documentation, or guardrails where needed to prevent regressions.
5. Leaves a concise audit summary describing what was reviewed, what was changed, what was deferred, and what still needs manual verification.

## Required Review Scope

The agent must inspect the current repository rather than relying on assumptions. Review at least these areas when they exist:

- Page structure, landmarks, heading hierarchy, semantic HTML, and content organization.
- Interactive controls, buttons, links, menus, dialogs, drawers, popovers, tabs, disclosures, drag-and-drop surfaces, and custom widgets.
- Forms, validation messages, error states, helper text, required indicators, autocomplete behavior, and input labeling.
- Focus order, focus visibility, focus restoration, trapped focus, skip navigation, and keyboard-only workflows.
- Screen-reader support including names, roles, values, live regions, announcements, aria usage, and duplicate or missing accessible text.
- Color contrast, status indicators, reduced-motion concerns, responsive zoom behavior, hit targets, and visual-only meaning.
- Frontend rendering logic, reusable UI primitives, design-system components, CSS utilities, and shared wrappers that influence accessibility across the app.
- Tests, linting rules, component stories, or validation tooling that can help detect or prevent future accessibility regressions.

## Execution Rules

The agent should follow this workflow:

1. Discover the current stack first.
   Identify the active languages, frameworks, package managers, UI layers, shared component patterns, and validation tools before proposing fixes.
2. Prioritize by user impact and breadth.
   Fix issues that block keyboard use, break screen-reader understanding, hide focus, prevent form completion, or affect shared components before lower-impact polish.
3. Apply changes when the correct remediation is clear.
   Do not stop at reporting problems if the issue can be safely fixed in this repository.
4. Prefer root-cause fixes.
   Favor semantic markup, shared component improvements, better defaults, and centralized accessibility behavior over one-off patches.
5. Stay conservative with risky UI rewrites.
   If a change would alter product behavior, layout strategy, or design-system direction materially, document it clearly and defer rather than guessing.
6. Validate the work.
   Run the relevant tests, lint checks, type checks, builds, accessibility tooling, or targeted manual verification steps available for the discovered stack.

## Expected Deliverables

The agent should leave behind:

- Code changes for accessibility fixes that are safe to apply now.
- Regression coverage or focused validation for accessibility-sensitive behavior where practical.
- Documentation or shared guidance updates when operational accessibility behavior changes.
- A summary grouped by outcome: fixed in this pass; still open and why; human/manual follow-up needed.

## Minimum Reporting Format

In the final summary, include:

1. Stack discovered
2. Accessibility surfaces reviewed
3. Findings fixed
4. Findings deferred
5. Validation performed
6. Manual verification still recommended
7. Follow-up actions required

## Preferred Fix Patterns

When applicable, prefer changes like:

- Replacing non-semantic wrappers with semantic elements where behavior already matches.
- Adding or correcting accessible names, labels, descriptions, and status text.
- Fixing focus order, visible focus, and focus restoration.
- Improving keyboard support for custom interactive components.
- Replacing fragile aria workarounds with simpler semantic patterns.
- Moving accessibility behavior into shared components when the issue is repeated.
- Reducing visual-only communication by adding text, labels, or state announcements.
- Respecting reduced-motion preferences and avoiding unnecessary motion burden.
- Adding targeted tests or validation for important accessible interactions.

## Out of Scope

Do not spend this pass on broad design rewrites unless they are required to remove a concrete accessibility blocker. Prefer targeted, explainable improvements that can be merged safely in an active codebase.

## Success Criteria

This issue is complete when:

- The custom GitHub agent has reviewed the live #codebase rather than a stale assumed stack.
- Meaningful accessibility improvements have been applied, not just reported.
- Relevant validation has been run for the discovered stack.
- Remaining gaps are documented with clear rationale, manual verification needs, and next actions.
