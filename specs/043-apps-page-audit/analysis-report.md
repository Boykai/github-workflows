# Specification Analysis Report: Apps Page Audit (043)

**Generated**: 2026-03-16  
**Artifacts Analyzed**: spec.md, tasks.md, constitution.md  
**Feature**: `043-apps-page-audit`

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution | CRITICAL | specs/043-apps-page-audit/ | **Missing `plan.md` artifact**. Constitution Phase-Based Execution (§Workflow Standards) requires Specify → Plan → Tasks. `tasks.md` was generated without `plan.md` existing. The `tasks.md` header confirms: "Prerequisites: spec.md (required for user stories)" — plan.md is not listed. | Run `/speckit.plan` to generate plan.md (with research.md, data-model.md, contracts/, quickstart.md) before proceeding to implementation. |
| C2 | Constitution | CRITICAL | specs/043-apps-page-audit/ | **Missing Constitution Check section**. Constitution §Compliance Review: "All feature plan.md files MUST include a Constitution Check section." Since plan.md does not exist, no constitution compliance evaluation has been performed. | Generate plan.md via `/speckit.plan`; ensure it includes a Constitution Check section evaluating all 5 principles. |
| H1 | Coverage | HIGH | spec.md:FR-010 | **FR-010 (form field labels) has no explicit task.** FR-010: "All form fields MUST have associated labels (visible or via ARIA attributes)." US2 ARIA tasks (T025–T031) cover dialog-level and button ARIA attributes but no task specifically adds `aria-label` or visible labels to `<input>`, `<select>`, or `<textarea>` elements in the Create App dialog. | Add a task in Phase 4 (US2) to audit and add labels to all form fields in the Create App dialog in `AppsPage.tsx`. |
| H2 | Coverage | HIGH | spec.md:Edge Cases (L108) | **Edge case "duplicate app name" has no task.** Spec edge case: "What happens when the user creates an app with a name that already exists? The system should display a clear conflict error message." No implementation task addresses handling 409/conflict errors distinctly from generic create errors. | Add a task in Phase 3 (US1) to detect and display a specific conflict error message when app creation fails due to a duplicate name. |
| H3 | Coverage | HIGH | spec.md:Edge Cases (L112) | **Edge case "non-existent detail URL" has no implementation task.** Spec: "When the user navigates directly to a detail view URL for an app that does not exist, display a clear 'app not found' message." T013 adds a retry button to AppDetailView error state but does not specifically address the 404/not-found scenario with navigation back to the list. | Add a task in Phase 3 (US1) to implement a dedicated "app not found" state in `AppDetailView.tsx` with a "Back to apps" navigation link. |
| H4 | Duplication | HIGH | tasks.md:T062, T098 | **Duplicate tasks for "no duplicate API calls."** T062 [US3]: "Verify no duplicate API calls between AppsPage.tsx and AppDetailView.tsx." T098 [US5]: "Verify no duplicate API calls — AppDetailView should use the same query instance as page or use useApp(name) without overlapping with page-level useApps()." Nearly identical scope and wording. | Remove T098 and keep T062 (US3, earlier phase). Add a cross-reference note in US5 that this was already addressed. |
| M1 | Coverage | MEDIUM | spec.md:Edge Cases (L114) | **Edge case "stale tab" has no task.** Spec: "What happens when the user has the Apps page open in two tabs and deletes an app in one?" No task addresses stale data handling across tabs. React Query's `refetchOnWindowFocus` may handle this implicitly but no task verifies it. | Add a verification task in Phase 7 (US5) to confirm `refetchOnWindowFocus` is enabled or add explicit stale-data handling. |
| M2 | Coverage | MEDIUM | spec.md:Edge Cases (L115) | **Edge case "iframe failure" has no implementation task.** Spec: "When the live preview iframe fails to load or the app port is not yet assigned, a clear placeholder or error state should appear." T081 tests AppPreview states but no implementation task adds the fallback. | Add an implementation task in Phase 3 (US1) for AppPreview error/loading fallback states in `AppPreview.tsx`. |
| M3 | Underspecification | MEDIUM | spec.md:L10, L22, L110, L114 | **Vague term "gracefully" used 4 times without measurable criteria.** Appears in: US1 acceptance scenario 8, edge cases for null fields, large lists, and stale tabs. "Gracefully" is not testable — no measurable behavior specified. | Replace each instance with specific behavior: e.g., "renders fallback UI without crashing" or "displays a placeholder message." |
| M4 | Underspecification | MEDIUM | tasks.md:T099 | **Assessment-only task may leave US5 AS-3 unresolved.** T099: "Assess whether pagination or virtualization is needed for >50 apps." US5 acceptance scenario 3 requires the interface to "handle the volume gracefully." An assessment task does not guarantee implementation if the assessment concludes pagination is needed. | Split T099 into: (a) assess need, (b) implement pagination/virtualization if threshold is met. |
| M5 | Inconsistency | MEDIUM | tasks.md:L38, T082–T091 | **AppPage.test.tsx (34 lines, 2 tests) not referenced in any task.** The Current Architecture table lists `AppPage.test.tsx` as a separate file from `AppsPage.test.tsx`. No task updates, expands, or validates `AppPage.test.tsx`. It may become stale after audit changes. | Add a task in Phase 6 (US4) to review and update `AppPage.test.tsx` or merge its tests into `AppsPage.test.tsx`. |
| M6 | Underspecification | MEDIUM | spec.md:SC-010 | **SC-010 threshold not reflected in tasks.** SC-010: "Users can create a new app and see it appear in the list within 3 seconds of successful creation." No task implements or measures this latency target. Query invalidation (implicit in React Query `onSuccess`) may satisfy it but no task verifies. | Add a verification task in Phase 8 to confirm list refresh occurs within 3 seconds after app creation (via `invalidateQueries` on mutation success). |
| L1 | Duplication | LOW | tasks.md:T069, T104 | **Overlapping Card component tasks.** T069 [US3]: "Replace custom card styling with shared Card component." T104 [Phase 8]: "Verify content sections use shared Card component." T104 is a validation of T069. Intentional but could be noted as a checkpoint rather than a standalone task. | Annotate T104 as a checkpoint/validation of T069 to clarify it's not redundant work. |
| L2 | Ambiguity | LOW | spec.md:L6 | **"Zero bugs" claim in TL;DR.** "Comprehensive audit... and zero bugs" is an unrealistic absolute. All software has latent defects. | Reword to "minimize known bugs" or "resolve all identified defects." |
| L3 | Coverage | LOW | spec.md:Edge Cases (L116) | **Edge case "whitespace-only form values" partially covered.** T091 tests whitespace rejection but no implementation task adds trim validation to the Create App form. If existing validation already trims, this is a non-issue. | Add a verification task or implementation task for trim validation on form submission if not already present. |

---

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (loading-indicator) | ✅ | T009, T010 | |
| FR-002 (error-with-retry-and-rate-limit) | ✅ | T008, T011, T012, T013 | |
| FR-003 (empty-state) | ✅ | T014 | |
| FR-004 (confirmation-dialogs) | ✅ | T015, T016, T017, T018, T019 | |
| FR-005 (success-feedback) | ✅ | T020, T021 | |
| FR-006 (user-friendly-errors) | ✅ | T004, T005, T006, T043 | |
| FR-007 (error-boundary) | ✅ | T022 | |
| FR-008 (keyboard-accessible) | ✅ | T025–T036 | Implicit via ARIA + focus tasks |
| FR-009 (dialog-focus-trap) | ✅ | T032, T033 | |
| FR-010 (form-field-labels) | ⚠️ | — | **No explicit task** (see H1) |
| FR-011 (aria-attributes) | ✅ | T025–T031 | |
| FR-012 (focus-indicators) | ✅ | T034, T035, T036 | |
| FR-013 (decorative-icons-hidden) | ✅ | T029 | |
| FR-014 (truncation-with-tooltip) | ✅ | T039, T040 | |
| FR-015 (verb-based-labels) | ✅ | T037, T038 | |
| FR-016 (timestamps-formatted) | ✅ | T041, T042 | |
| FR-017 (dark-mode) | ✅ | T044–T048 | |
| FR-018 (responsive-layout) | ✅ | T049, T050, T051 | |
| FR-019 (design-system-spacing) | ✅ | T103 | |
| FR-020 (card-component) | ✅ | T069, T104 | |
| FR-021 (page-250-lines) | ✅ | T053 | |
| FR-022 (hook-extraction) | ✅ | T056 | |
| FR-023 (no-any-types) | ✅ | T007, T057, T058, T059, T060 | |
| FR-024 (query-key-conventions) | ✅ | T061, T063 | |
| FR-025 (no-duplicate-api-calls) | ✅ | T062, T098 | T098 duplicates T062 (see H4) |
| FR-026 (stable-keys) | ✅ | T094, T095 | |
| FR-027 (lint-zero-warnings) | ✅ | T071, T105 | |
| FR-028 (alias-imports) | ✅ | T066 | |
| FR-029 (no-dead-code) | ✅ | T064, T065 | |
| FR-030 (hook-tests) | ✅ | T074, T075, T076, T077 | |
| FR-031 (component-tests) | ✅ | T078–T086 | |
| FR-032 (edge-case-tests) | ✅ | T087–T091 | |
| FR-033 (finalized-copy) | ✅ | T102 | |

---

## Constitution Alignment

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ Pass | spec.md has prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and clear scope. |
| II. Template-Driven Workflow | ⚠️ Partial | spec.md follows canonical template. tasks.md follows template. **plan.md is missing entirely** — template cannot be evaluated. |
| III. Agent-Orchestrated Execution | ⚠️ Violation | Phase-Based Execution requires Plan phase before Tasks phase. Tasks were generated without plan.md. |
| IV. Test Optionality with Clarity | ✅ Pass | Tests explicitly requested in spec (FR-030, FR-031, FR-032). US4 covers test coverage. tasks.md header documents test requirement. |
| V. Simplicity and DRY | ✅ Pass | No premature abstraction. Task T053 correctly assesses line count before extraction. Minor duplication (T062/T098) noted. |
| Constitution Check in plan.md | ❌ Missing | No plan.md exists, so no Constitution Check has been performed. |

---

## Unmapped Tasks

All 108 tasks map to a requirement, user story, or validation checkpoint. No orphaned tasks detected.

However, the following tasks serve as cross-phase validation checkpoints (not direct FR implementations):

| Task | Purpose |
|------|---------|
| T001, T002, T003 | Baseline audit (Phase 1 setup) |
| T024, T052, T073, T093, T101, T107 | Regression test runs after each story |
| T105, T106, T108 | Final lint, type check, and manual validation |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 33 |
| Total Tasks | 108 |
| Coverage % (FRs with ≥1 task) | **97%** (32/33) |
| Uncovered Requirements | 1 (FR-010) |
| Edge Cases in Spec | 9 |
| Edge Cases with Task Coverage | 5 of 9 (56%) |
| User Stories | 5 (US1 P1, US2 P2, US3 P2, US4 P3, US5 P3) |
| Phases | 8 |
| Parallelizable Tasks [P] | ~75 of 108 |
| Ambiguity Count | 2 (M3, L2) |
| Duplication Count | 2 (H4, L1) |
| Critical Issues | 2 (C1, C2 — both related to missing plan.md) |
| High Issues | 4 |
| Medium Issues | 6 |
| Low Issues | 3 |
| Total Issues | 15 |

---

## Next Actions

### ❌ CRITICAL issues exist — resolve before `/speckit.implement`

1. **Run `/speckit.plan`** to generate `plan.md` and associated artifacts (research.md, data-model.md, contracts/, quickstart.md). This is **blocking** — constitution requires plan phase completion before tasks execution.
2. **Verify the generated plan.md includes a Constitution Check section** evaluating all 5 principles.
3. After plan.md is generated, optionally re-run `/speckit.tasks` to ensure tasks align with any architectural decisions in the plan.

### Recommended fixes before implementation:

4. **Add task for FR-010** (form field labels in Create App dialog) — insert after T031 in Phase 4.
5. **Add tasks for uncovered edge cases**: duplicate app name conflict error (Phase 3), non-existent detail URL "app not found" state (Phase 3), iframe error fallback in AppPreview (Phase 3).
6. **Remove duplicate task T098** — T062 already covers duplicate API call verification.
7. **Split T099** into assessment + conditional implementation to ensure US5 AS-3 is resolved.
8. **Add task for AppPage.test.tsx** review/update in Phase 6 to prevent test file staleness.

### If only LOW/MEDIUM remain after fixes:

- Proceed to `/speckit.implement` with the understanding that "gracefully" language in spec should be interpreted as "renders fallback UI without crashing."
- SC-010 (3-second refresh) can be verified as part of Phase 8 manual browser check.

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 6 issues (C1, C2, H1, H2, H3, H4)? I will not apply them automatically — explicit approval is required before any follow-up editing.
