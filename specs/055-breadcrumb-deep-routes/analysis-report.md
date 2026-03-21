# Specification Analysis Report: Breadcrumb Deep Route Support

**Feature**: `055-breadcrumb-deep-routes` | **Date**: 2026-03-21  
**Artifacts Analyzed**: `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `contracts/breadcrumb-context.md`, `research.md`  
**Constitution**: `.specify/memory/constitution.md` v1.0.0

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | HIGH | spec.md:L75, spec.md:L87 | FR-002 ("all non-final segments as clickable links") conflicts with edge case ("non-navigable intermediate paths should be non-clickable text"). These two statements impose contradictory rendering behavior for intermediate segments that have no page. | Resolve conflict: either amend FR-002 to add an exception for non-navigable paths, or remove the edge case. If FR-002 is amended, add a task to implement non-navigable path detection. |
| F2 | Underspecification | HIGH | tasks.md:L64 | T006 places breadcrumb label registration in `AppsPage.tsx`, but the app's `display_name` is fetched by the embedded `AppDetailView` component (via `useApp(appName)` in `src/components/apps/AppDetailView.tsx`). `AppsPage.tsx` does not call `useApp` — it only has the apps list query. T006 would need either a duplicate query in `AppsPage.tsx` or the registration should happen inside `AppDetailView`. | Clarify where label registration belongs: either add `useApp(appName)` call in `AppsPage.tsx` (TanStack Query deduplicates automatically) or move label registration to `AppDetailView.tsx`. |
| F3 | Ambiguity | MEDIUM | spec.md:L104 | SC-003 uses "standard navigation response time" — no measurable threshold defined. This acceptance criterion is untestable without a concrete metric. | Define a concrete threshold (e.g., "within 100ms") or reference an existing performance budget. |
| F4 | Ambiguity | MEDIUM | spec.md:L105 | SC-004 uses "without truncation or layout issues" — no measurable criteria for what constitutes a "layout issue." | Define specific criteria (e.g., "all segments visible without horizontal scrolling at viewport widths ≥ 1024px"). |
| F5 | Inconsistency | MEDIUM | plan.md:L27 | Plan Scale/Scope says "3 new files (context, provider, hook)" but Project Structure (L63–69) and File Change Summary (L190–196) list only 2 new files: `useBreadcrumb.ts` and `breadcrumb-utils.ts`. The context, provider, and hook all reside in `useBreadcrumb.ts`. | Correct Scale/Scope to "2 new files (hook + utility)." |
| F6 | Coverage Gap | MEDIUM | spec.md:L75, tasks.md (absent) | Edge case "non-navigable intermediate path renders as non-clickable text" has no corresponding task. Current implementation (T004/T005) will render all non-final segments as clickable links per FR-002. | Blocked by F1 resolution. If FR-002 is amended, add a task for non-navigable path detection. If edge case is removed, no action needed. |
| F7 | Underspecification | MEDIUM | spec.md (absent section) | No Non-Functional Requirements section in spec.md. Performance expectations ("single React commit," "no perceptible delay") appear only in plan.md (L25), not formalized in the spec. Note: the spec template (`spec-template.md`) also lacks an NFR section — this is a systemic template gap. | Either add an NFR section to spec.md with measurable performance criteria, or document that performance is covered informally by plan-level guidance. Consider updating the spec template. |
| F8 | Underspecification | LOW | tasks.md:L80, L96 | T007 and T008 are verification-only tasks ("Verify that…") with no implementation action. If verification reveals issues, there's no remediation guidance. | Add contingency notes: "If verification fails, update `buildBreadcrumbSegments` to handle [specific case]." |
| F9 | Duplication | LOW | spec.md:L21, spec.md:L68 | US1 scenario 2 ("on `/apps`, breadcrumb shows Home > Apps") and US4 scenario 1 ("route `/apps` has label 'Apps', breadcrumb displays 'Home > Apps'") test the same observable behavior from different user story angles. | Acceptable overlap — US1 tests segment rendering preservation, US4 tests label resolution source. No action needed. |
| F10 | Coverage Gap | LOW | spec.md:L77, tasks.md (absent) | Edge case "multiple components set labels for same segment — last label wins" has no explicit task. Implicitly handled by `Map.set()` last-writer-wins semantics. | No action needed — Map semantics naturally satisfy this. Consider adding a comment in `useBreadcrumb.ts` documenting this implicit behavior. |
| F11 | Underspecification | LOW | spec.md (absent section) | No explicit "Out of Scope" section. Constitution requires "clear scope boundaries and out-of-scope declarations." Assumptions section (L109–117) partially bounds scope. Note: spec template also lacks this section. | Consider adding an "Out of Scope" section listing exclusions (e.g., breadcrumb persistence, server-side rendering, mobile truncation, breadcrumb schema/JSON-LD). |
| F12 | Ambiguity | LOW | plan.md:L25 | Performance goal uses "no perceptible delay" — subjective measurement without a concrete threshold. | Replace with measurable criterion if promoting to a formal NFR. Acceptable as informal plan guidance. |

---

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (parse-segments) | ✅ | T004, T005 | Core implementation |
| FR-002 (clickable-intermediate) | ✅ | T005 | Conflicts with edge case (see F1) |
| FR-003 (final-nonclickable) | ✅ | T005 | |
| FR-004 (context-api) | ✅ | T002, T003 | |
| FR-005 (context-label-display) | ✅ | T005, T006 | |
| FR-006 (navroutes-label) | ✅ | T004, T008 | |
| FR-007 (titlecase-fallback) | ✅ | T001, T004 | |
| FR-008 (label-cleanup) | ✅ | T002, T006, T011 | |
| FR-009 (arbitrary-depth) | ✅ | T004, T007 | |
| FR-010 (ignore-query-hash) | ✅ | T010 | Handled by `useLocation().pathname` |
| FR-011 (trailing-slash) | ✅ | T004, T009 | |
| FR-012 (dynamic-update) | ✅ | T005 | SPA navigation via React Router |

### User Story Coverage

| Story | Priority | Covered By | Status |
|-------|----------|------------|--------|
| US1 — Multi-Segment Trail | P1 | T004, T005 | ✅ Direct implementation |
| US2 — Dynamic Labels | P1 | T006 | ✅ Direct implementation |
| US3 — Three+ Levels | P2 | T007 | ✅ Satisfied by T004 (validation only) |
| US4 — Static Route Labels | P2 | T008 | ✅ Satisfied by T004 (validation only) |

---

## Constitution Alignment

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | 4 prioritized user stories (P1×2, P2×2), Given-When-Then scenarios, 12 FRs, edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Specify → Plan → Tasks → Analyze pipeline followed |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not requested; documented in tasks.md header |
| V. Simplicity and DRY | ✅ PASS | React Context only, no new dependencies, pure utility functions |

**Note**: Constitution requires "clear scope boundaries and out-of-scope declarations" (Principle I). The spec lacks an explicit Out-of-Scope section; however, the Assumptions section provides implicit scope boundaries. The spec template itself also omits this section — recommend updating the template in a future constitution amendment (see F11).

---

## Unmapped Tasks

None — all 12 tasks (T001–T012) map to at least one functional requirement or user story.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 12 |
| Total User Stories | 4 (2 P1, 2 P2) |
| Total Tasks | 12 (T001–T012) |
| Requirement Coverage | **100%** (12/12 FRs have ≥1 task) |
| Ambiguity Count | 3 (F3, F4, F12) |
| Duplication Count | 1 (F9 — acceptable overlap) |
| Critical Issues | **0** |
| HIGH Issues | **2** (F1, F2) |
| MEDIUM Issues | **5** (F3, F4, F5, F6, F7) |
| LOW Issues | **5** (F8, F9, F10, F11, F12) |
| Total Findings | **12** |

---

## Next Actions

### Recommended Before `/speckit.implement`

1. **Resolve F1 (HIGH — FR-002 vs edge case conflict)**: Decide whether non-navigable intermediate paths should be clickable or not. Either:
   - Amend FR-002 to add an exception: "…except segments whose cumulative path does not match a defined route, which SHOULD render as non-clickable text"
   - Or remove the edge case and keep FR-002 as-is (all non-final segments are always clickable — simpler, per Principle V)
   - **Suggested command**: `Run /speckit.specify with refinement to resolve FR-002 vs edge case conflict`

2. **Resolve F2 (HIGH — T006 data access)**: Clarify whether breadcrumb label registration for the app detail view should:
   - Stay in `AppsPage.tsx` with an added `useApp(appName)` call (TanStack Query deduplication makes this safe), or
   - Move to `AppDetailView.tsx` where `display_name` is already available
   - **Suggested command**: `Manually edit tasks.md to update T006 file reference and data access strategy`

### Optional Improvements (Can Proceed Without)

3. **F3/F4 — Measurable success criteria**: Add concrete thresholds to SC-003 and SC-004 if formal acceptance testing is planned
4. **F5 — File count correction**: Update plan.md Scale/Scope from "3 new files" to "2 new files"
5. **F7 — Template gap**: Consider adding NFR and Out-of-Scope sections to `spec-template.md` via `/speckit.constitution` amendment

### Verdict

No CRITICAL issues found. Two HIGH issues should be resolved before implementation to avoid ambiguity during coding. All functional requirements have full task coverage (100%). The artifacts are well-structured and internally consistent aside from the findings above. The feature can proceed to `/speckit.implement` after addressing F1 and F2.

---

*Would you like me to suggest concrete remediation edits for the top issues (F1 and F2)?*
