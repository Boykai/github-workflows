# Specification Analysis Report: Tools Page Audit

**Feature**: `043-tools-page-audit` | **Date**: 2026-03-16  
**Artifacts Analyzed**: spec.md, plan.md, tasks.md, constitution.md, data-model.md, research.md, contracts/component-contracts.md, checklists/requirements.md

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | HIGH | research.md:L22,L37,L40,L182; plan.md:L174,L186; tasks.md:L39,L53-55; quickstart.md:L48,L130 | `isRateLimitApiError()` import path documented as `@/services/api` across all artifacts, but function actually lives at `@/utils/rateLimit` (verified in source) | Update all references from `@/services/api` → `@/utils/rateLimit`. Tasks T005, T006, T007, T008 all point implementers to the wrong file |
| C1 | Coverage Gap | HIGH | plan.md:L57,L98-99; tasks.md (absent) | Plan identifies `useRepoMcpConfig` and `useMcpPresets` as hooks needing tests (plan.md L57, L98-99) but tasks.md contains zero test tasks for either hook. FR-022 mandates "Custom hooks MUST have automated tests" | Add T036a/T036b: Write hook tests for `useRepoMcpConfig` and `useMcpPresets` in dedicated test files |
| C2 | Coverage Gap | HIGH | plan.md:L162-164; tasks.md:L27-28,L139 | Plan project structure and task lint/validation commands omit `useRepoMcpConfig.ts` (72 lines) and `useMcpPresets.ts` (21 lines) — only `useTools.ts` and `useAgentTools.ts` are listed. These hooks are core to ToolsPanel and imported directly | Add `src/hooks/useRepoMcpConfig.ts` and `src/hooks/useMcpPresets.ts` to plan project structure and to T040/T003 lint commands |
| C3 | Coverage Gap | HIGH | tasks.md:L139 (T040); plan.md:L241 | T040 lint command (`npx eslint ... src/hooks/useTools.ts src/hooks/useAgentTools.ts`) excludes `useRepoMcpConfig.ts` and `useMcpPresets.ts` from lint validation scope | Expand T040 lint command to include `src/hooks/useRepoMcpConfig.ts src/hooks/useMcpPresets.ts` |
| U1 | Underspecification | MEDIUM | spec.md:L134 (FR-018); tasks.md:L131 (T032) | FR-018 says "The Tools page file MUST be no more than 250 lines; larger sections MUST be extracted." T032 only verifies ToolsPage.tsx (84 lines). ToolsPanel.tsx (398 lines) and UploadMcpModal.tsx (428 lines) both exceed 250 lines with no decomposition task | Clarify FR-018 scope: if "page file" means only ToolsPage.tsx, this passes. If it includes primary sub-components, add decomposition tasks for ToolsPanel and UploadMcpModal. Plan risk R4 acknowledges UploadMcpModal size but no task exists |
| A1 | Ambiguity | MEDIUM | spec.md:L130 (FR-014); contracts/component-contracts.md:L85 | FR-014 requires truncation for "long text" but provides no measurable threshold. Contracts define `max-w-[200px]` — an arbitrary Tailwind value that conflicts with the parent issue's "no arbitrary values like p-[13px]" guideline | Define truncation width using standard Tailwind scale values (e.g., `max-w-xs` = 320px) or specify character count threshold |
| C4 | Coverage Gap | MEDIUM | spec.md:L105-111 (Edge Cases); tasks.md:L138 (T039) | 4 of 7 spec edge cases have no dedicated implementation or test task: (1) session expiry mid-operation, (2) unexpected API response shape, (3) tool assigned to since-deleted agents, (4) unexpected MCP JSON keys. T039 only covers rate-limit, null data, long strings, and rapid clicks | Add edge case handling tasks or expand T039 description to explicitly cover missing edge cases |
| U2 | Underspecification | MEDIUM | tasks.md:L117 (T031); plan.md:L222 | T031 says "Add pagination or load-more pattern" for >50 tools but doesn't specify which pattern. Plan says "consider react-window or pagination" without resolving. This leaves an implementation decision unresolved | Resolve in plan: choose pagination (simpler, aligns with Simplicity principle) or virtualization (better UX for large lists). Document rationale in Key Decisions |
| D1 | Underspecification | MEDIUM | plan.md:L57; tasks.md (absent) | Plan lists `UploadMcpModal` as a "key component" requiring tests (plan.md L57) but tasks.md has no test task for UploadMcpModal. Only ToolsPanel (T037) and ToolCard (T038) have component test tasks | Add a task for UploadMcpModal component tests if plan's intention holds, or remove UploadMcpModal from the plan's test scope list |
| F2 | Inconsistency | LOW | plan.md:L66-77 (Component Inventory) | Plan line counts differ from actual source: ToolsPanel 399→398, ToolCard 122→121, UploadMcpModal 429→428 (off-by-one each); ToolChips ~60→45 (15-line discrepancy). Minor but could confuse implementers | Update line counts to match actual source. ToolChips discrepancy (45 vs ~60) is notable |
| F3 | Inconsistency | LOW | plan.md:L200 (Phase 2, task 2.4) | Plan refers to "SyncStatusBadge (ToolCard)" as if it's a standalone component. It is actually an internal function within ToolCard.tsx (line 21). Tasks correctly reference ToolCard.tsx | Update plan to clarify SyncStatusBadge is an inline function within ToolCard, not a separate file |
| U3 | Underspecification | LOW | tasks.md:L133 (T033) | T033 "Verify all complex state logic (>15 lines)" doesn't specify which files to audit beyond `useTools.ts`. ToolsPanel.tsx (398 lines) likely has inline state logic that should be evaluated | Expand T033 to explicitly list files to audit: ToolsPanel.tsx, UploadMcpModal.tsx, EditRepoMcpModal.tsx |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (loading-indicator) | ✅ | T006, T007, T009 | Three components covered |
| FR-002 (error-message-retry) | ✅ | T006, T007, T009 | Retry action included in each |
| FR-003 (rate-limit-detection) | ✅ | T006, T007, T008 | ⚠️ All reference wrong import path (F1) |
| FR-004 (empty-state) | ✅ | T007, T009 | McpPresetsGallery and tools list |
| FR-005 (independent-section-loading) | ✅ | T010 | Explicit verification task |
| FR-006 (confirmation-dialogs) | ✅ | T011, T012 | Tool delete + repo server delete |
| FR-007 (success-feedback) | ✅ | T013 | Upload, edit, sync, delete mutations |
| FR-008 (error-message-format) | ✅ | T008, T027 | Hook formatting + silent catch fix |
| FR-009 (keyboard-accessible) | ✅ | T020 | Cross-component keyboard verification |
| FR-010 (modal-focus-trapping) | ✅ | T021 | Three modals covered |
| FR-011 (form-field-labels) | ✅ | T014, T015 | UploadMcpModal + ToolSelectorModal |
| FR-012 (status-indicators) | ✅ | T016 | Text + color in ToolCard |
| FR-013 (verb-based-labels) | ✅ | T022 | Cross-component audit |
| FR-014 (truncation-tooltip) | ✅ | T023, T024 | ToolCard + RepoConfigPanel |
| FR-015 (timestamp-format) | ✅ | T025 | Relative/absolute threshold |
| FR-016 (responsive-layout) | ✅ | T028 | Four viewport widths tested |
| FR-017 (dark-mode) | ✅ | T026 | Cross-component audit |
| FR-018 (page-file-250-lines) | ✅ | T032 | ⚠️ Only checks ToolsPage.tsx (84L); ToolsPanel (398L) and UploadMcpModal (428L) not addressed (U1) |
| FR-019 (hook-extraction) | ✅ | T033 | ⚠️ Scope unclear — only references useTools.ts (U3) |
| FR-020 (zero-lint-type-errors) | ✅ | T040, T042 | ⚠️ Lint scope excludes useRepoMcpConfig.ts, useMcpPresets.ts (C3) |
| FR-021 (no-any-dead-code) | ✅ | T034 | Cross-file cleanup |
| FR-022 (test-coverage) | ⚠️ Partial | T036, T037, T038, T039 | ⚠️ Missing tests for useRepoMcpConfig, useMcpPresets, UploadMcpModal (C1, D1) |
| FR-023 (icon-accessibility) | ✅ | T017, T018 | Preset buttons + cross-component icons |
| FR-024 (focus-indicators) | ✅ | T019 | Cross-component focus ring audit |

---

## Constitution Alignment Issues

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md contains 5 prioritized user stories (P1–P3), Given-When-Then scenarios, 7 edge cases, 24 FRs, 12 success criteria |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates; no unjustified custom sections |
| III. Agent-Orchestrated Execution | ✅ PASS | Specify → Plan → Tasks → Analyze chain followed correctly |
| IV. Test Optionality with Clarity | ⚠️ PARTIAL | Tests are explicitly mandated by FR-022. Plan correctly identifies hooks needing tests (useToolsList, useRepoMcpConfig, useMcpPresets) but tasks.md only covers useToolsList. Two of three required hook test tasks are missing (C1) |
| V. Simplicity and DRY | ✅ PASS | All improvements use existing shared components. No new dependencies or abstractions. Complexity Tracking section confirms no violations |

**Constitution Conflicts**: None at CRITICAL severity. Principle IV has a gap (C1) at HIGH severity — plan acknowledges test requirements for 3 hooks but tasks only implement 1.

---

## Unmapped Tasks

All 44 tasks (T001–T044) map to at least one requirement, user story, or cross-cutting concern. No orphan tasks detected.

| Task | Mapping |
|------|---------|
| T001–T003 | Setup/infrastructure (no FR mapping needed) |
| T004–T005 | Foundational audit (no FR mapping needed) |
| T006–T013 | US1 → FR-001 through FR-008 |
| T014–T021 | US2 → FR-009 through FR-012, FR-023, FR-024 |
| T022–T027 | US3 → FR-013 through FR-015, FR-017, FR-008 |
| T028–T031 | US4 → FR-016 (responsive) + performance |
| T032–T040 | US5 → FR-018 through FR-022 |
| T041–T044 | Polish → ErrorBoundary, type-check, test suite, manual validation |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 24 |
| Total Tasks | 44 |
| Coverage % (FRs with ≥1 task) | 100% (24/24) |
| Coverage % (FRs with complete task coverage) | 87.5% (21/24) — FR-018, FR-020, FR-022 have partial gaps |
| Ambiguity Count | 2 (A1, U2) |
| Duplication Count | 0 |
| Underspecification Count | 4 (U1, U2, U3, D1) |
| Inconsistency Count | 3 (F1, F2, F3) |
| Coverage Gap Count | 4 (C1, C2, C3, C4) |
| Critical Issues | 0 |
| High Issues | 4 (F1, C1, C2, C3) |
| Medium Issues | 5 (U1, A1, C4, U2, D1) |
| Low Issues | 3 (F2, F3, U3) |
| Total Findings | 12 |
| User Stories | 5 |
| Edge Cases in Spec | 7 |
| Edge Cases with Task Coverage | 3 of 7 (43%) |
| Constitution Principles Satisfied | 5/5 (1 partial: Principle IV) |

---

## Next Actions

### Before `/speckit.implement` (recommended — resolve HIGH issues)

1. **Fix F1**: Update `isRateLimitApiError()` import path from `@/services/api` to `@/utils/rateLimit` in research.md, plan.md, quickstart.md, tasks.md (T005, T006, T007, T008), and contracts/component-contracts.md. Without this fix, implementers will look for the function in the wrong file.

2. **Fix C1+C2+C3**: Add missing hooks to scope:
   - Add `useRepoMcpConfig.ts` and `useMcpPresets.ts` to plan.md project structure (L162-164)
   - Add test tasks for `useRepoMcpConfig` and `useMcpPresets` hooks (extend T036 or add T036a/T036b)
   - Expand T040 lint command to include `src/hooks/useRepoMcpConfig.ts src/hooks/useMcpPresets.ts`

### Proceed with caution (MEDIUM issues — can address during implementation)

3. **Clarify U1**: Decide whether FR-018's 250-line limit applies only to ToolsPage.tsx or also to primary sub-components (ToolsPanel 398L, UploadMcpModal 428L). If sub-components are included, add decomposition tasks.

4. **Resolve U2**: Choose pagination vs virtualization for T031. Recommend pagination for simplicity (Constitution Principle V).

5. **Expand C4**: Add explicit task coverage for the 4 uncovered edge cases, or expand T039 to enumerate them.

6. **Fix D1**: Either add UploadMcpModal component tests (consistent with plan) or remove it from plan's test scope list.

### Nice-to-have (LOW issues — optional)

7. **Fix F2**: Update plan.md line counts to match actual source (ToolChips: 45, not ~60).
8. **Clarify F3**: Note that SyncStatusBadge is an inline function in ToolCard.tsx, not a separate component file.
9. **Expand U3**: List specific files for T033's state logic audit.

---

## Remediation Summary

Would you like me to suggest concrete remediation edits for the top 4 HIGH issues (F1, C1, C2, C3)? These edits would update tasks.md, plan.md, research.md, and quickstart.md to correct the import path and add missing hook coverage. (Edits will NOT be applied automatically — approval required.)
