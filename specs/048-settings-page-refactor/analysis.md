# Specification Analysis Report: Settings Page Refactor with Secrets

**Feature**: `048-settings-page-refactor`
**Analyzed**: 2026-03-16
**Artifacts**: spec.md, plan.md, tasks.md
**Constitution**: v1.0.0 (2026-01-30)

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution | CRITICAL | plan.md (entire file) | **Missing Constitution Check section.** Constitution §Compliance Review (line 120–122) requires all `plan.md` files to include a "Constitution Check" section evaluating compliance with each principle. Plan template (lines 30–34) mandates this as a gate before Phase 0 research. The plan.md has no such section. | Add Constitution Check section to plan.md with pre-research and post-design gates evaluating each of the 5 core principles. Run `/speckit.plan` with refinement. |
| C2 | Constitution | CRITICAL | plan.md (entire file) | **Missing companion artifacts.** Plan template (lines 40–47) requires: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`. None exist in `specs/048-settings-page-refactor/`. Constitution §Phase-Based Execution requires each phase to complete before the next begins. | Generate missing companion artifacts via `/speckit.plan`. At minimum, create `research.md` (Phase 0) and `data-model.md` (Phase 1). |
| C3 | Constitution | CRITICAL | plan.md (entire file) | **Missing Technical Context section.** Plan template (lines 14–28) requires explicit Technical Context with Language/Version, Primary Dependencies, Storage, Testing, Target Platform, Performance Goals, Constraints, and Scale/Scope. Plan.md has a "Tech Stack" section but it does not match the required structure. | Restructure "Tech Stack" into the canonical Technical Context format per plan template. |
| C4 | Constitution | CRITICAL | plan.md (entire file) | **Missing Complexity Tracking section.** Plan template (lines 97–104) requires Complexity Tracking to justify any Constitution Check violations. This section is completely absent. | Add Complexity Tracking section to plan.md, even if empty ("No violations to justify"). |
| I1 | Inconsistency | HIGH | tasks.md:T012 (line 52), spec.md:L223 | **`require_session` does not exist.** T012 says "import `require_session` dependency from `solune/backend/src/api/dependencies.py`". Neither the function nor the file exists. The actual auth dependency is `get_session_dep` from `src.api.auth`. spec.md Assumptions (line 223) also references "existing `require_session` authentication dependency". | Update tasks.md T012 to reference `get_session_dep` from `solune/backend/src/api/auth.py`. Update spec.md Assumption to use correct function name. |
| I2 | Inconsistency | HIGH | plan.md:L37,79 vs tasks.md:T018 (line 61) | **Router registration location conflict.** Plan.md line 37 says `main.py — EDIT — register secrets router` and line 79 says "Register secrets router in `solune/backend/src/main.py`". Tasks.md T018 correctly says `solune/backend/src/api/__init__.py`. Verified: all routers are registered in `api/__init__.py`, not `main.py`. | Correct plan.md Project Structure and Phase 1 to reference `api/__init__.py` instead of `main.py`. |
| E1 | Coverage Gap | HIGH | spec.md:US7 (lines 119–132), tasks.md:T061–T068 | **Dead code `McpSettings.tsx` and `useMcpSettings.ts` not in cleanup scope.** Both files are confirmed dead code (only self-referencing imports). US7 cleanup list (spec.md line 131) does not include them. Tasks T061–T068 delete 6 files but miss these 2. SC-008 requires a decrease of at least 5 files — including these increases the margin. | Add `McpSettings.tsx` and `useMcpSettings.ts` to US7 cleanup scope in both spec.md and tasks.md. |
| E2 | Coverage Gap | MEDIUM | spec.md:SC-007 (line 238) | **No baseline measurement task for performance criterion.** SC-007 requires "initial load time does not increase by more than 10% compared to the pre-refactor baseline" but no task captures a baseline measurement before refactoring or validates the criterion after. | Add a task in Phase 1 to measure and record the pre-refactor Settings page load time, and a validation task in Phase 10 to compare post-refactor performance. |
| E3 | Coverage Gap | MEDIUM | spec.md:Edge Cases (lines 137, 143) | **Edge cases without explicit tasks.** Two edge cases have no corresponding tasks: (1) "user has no repositories" — T047 covers this. (2) "session expires on Secrets tab" with redirect-and-return behavior — no task addresses this. (3) "admin user ID is not configured" — no task explicitly handles this scenario beyond T034's admin check. | Add explicit tasks for session-expiry redirect behavior and unconfigured admin ID fallback, or document them as out-of-scope in spec.md. |
| E4 | Coverage Gap | MEDIUM | spec.md:SC-003 (line 234) | **No measurement task for 60-second round-trip criterion.** SC-003 requires secrets round-trip "in under 60 seconds" but no task includes a timing measurement or validation step. | Add a manual verification step in Phase 10 (T080) that explicitly includes timing the secrets round-trip. |
| U1 | Underspecification | MEDIUM | tasks.md:T035 (line 113) | **Vague implementation approach for unsaved changes preservation.** T035 says "use controlled tab state so tab content is not unmounted on switch, **or** use local state persistence" — the "or" leaves the approach undefined. FR-006 is a MUST requirement. | Specify a single approach in T035. Shadcn Tabs with `forceMount` on each `TabsContent` is the standard pattern. |
| U2 | Underspecification | MEDIUM | spec.md:SC-001 (line 232) | **"Within 2 clicks" lacks precise definition.** SC-001 says "Users can locate and modify their AI provider and model settings within 2 clicks" — does "navigate to Settings" count as a click? Does dropdown selection count? | Clarify SC-001 to specify the starting point (e.g., "from the Settings page") and what constitutes a "click" in this context. |
| A1 | Ambiguity | MEDIUM | spec.md:L223 | **Assumption references non-existent dependency name.** "The existing `require_session` authentication dependency provides adequate authorization" — function doesn't exist in codebase, creating confusion for implementers. | Correct to `get_session_dep` from `src.api.auth`. |
| D1 | Duplication | LOW | plan.md:Phase 1 vs Phase 5 | **Duplicate mention of test creation.** Plan.md Phase 1 item 4 mentions "Register router in main.py" (incorrect) and Phase 5 item 20 mentions tests. Tasks.md correctly separates these. Minor duplication in plan narrative vs tasks decomposition. | No action needed — tasks.md is the source of truth for execution. |
| D2 | Duplication | LOW | tasks.md:T069–T070 vs T077 | **Test tasks appear in both story-specific and polish phases.** T069–T070 create test files in Phase 10; T077 runs the full test suite also in Phase 10. This is intentional (create then validate) but could be consolidated. | No action needed — sequential create-then-run is correct. |
| S1 | Inconsistency | LOW | plan.md:L37 vs tasks.md:T018 | **`globalSettingsSchema.ts` listed as `.ts` among `.tsx` files.** Spec.md US7 line 131 lists active components mixing `.tsx` and `.ts` extensions. This is accurate (the file IS `.ts`) but may confuse reviewers expecting consistency. | No action needed — file extension is correct. |
| S2 | Inconsistency | LOW | tasks.md:Phase 2 header (line 36–38) | **Phase 2 blocking note is incomplete.** States "US3 and US6 depend on this phase being complete" but US3 also depends on US2 (tab structure). The Dependencies section (lines 253–258) correctly documents this. | Update Phase 2 header note to mention US2 dependency for completeness, or defer to the Dependencies section. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (tabbed-interface) | ✅ | T031 | |
| FR-002 (essential-default-tab) | ✅ | T031 | |
| FR-003 (url-hash-update) | ✅ | T031, T033 | |
| FR-004 (hash-fragment-activation) | ✅ | T032 | |
| FR-005 (admin-tab-visibility) | ✅ | T034 | |
| FR-006 (unsaved-changes-preservation) | ✅ | T035 | ⚠️ Underspecified approach (U1) |
| FR-007 (per-section-save) | ✅ | T051 | |
| FR-008 (essential-tab-content) | ✅ | T028, T030 | |
| FR-009 (no-signal-on-essential) | ✅ | T029 | |
| FR-010 (preferences-tab-content) | ✅ | T049 | |
| FR-011 (preferences-section-save) | ✅ | T050, T051 | |
| FR-012 (admin-tab-content) | ✅ | T053 | |
| FR-013 (admin-reuse-validation) | ✅ | T054 | |
| FR-014 (admin-fallback) | ✅ | T032 | |
| FR-015 (list-secrets-endpoint) | ✅ | T007, T014 | |
| FR-016 (set-secret-encrypted) | ✅ | T008, T009, T015 | |
| FR-017 (delete-secret-endpoint) | ✅ | T010, T016 | |
| FR-018 (auto-create-environment) | ✅ | T006, T015 | |
| FR-019 (secret-name-validation) | ✅ | T015 | |
| FR-020 (secret-value-size-limit) | ✅ | T013 | |
| FR-021 (secrets-auth-required) | ✅ | T014, T015, T016 | ⚠️ References wrong dependency name (I1) |
| FR-022 (repo-selector) | ✅ | T039 | |
| FR-023 (known-secrets-display) | ✅ | T040, T041 | |
| FR-024 (set-update-remove-actions) | ✅ | T041, T043, T044 | |
| FR-025 (custom-secret-form) | ✅ | T045 | |
| FR-026 (password-input-security) | ✅ | T042 | |
| FR-027 (prefix-warning) | ✅ | T045 | |
| FR-028 (preset-required-secrets) | ✅ | T057, T058 | |
| FR-029 (check-secrets-endpoint) | ✅ | T017, T027 | |
| FR-030 (tools-page-warning) | ✅ | T059 | |
| FR-031 (tabpanel-aria) | ✅ | T036, T074 | |
| FR-032 (secret-input-aria) | ✅ | T042, T075 | |
| FR-033 (tab-focus-management) | ✅ | T037 | |
| FR-034 (delete-redundant-components) | ✅ | T061–T066 | ⚠️ Missing McpSettings.tsx cleanup (E1) |
| FR-035 (update-tests) | ✅ | T068, T073 | |

---

## Constitution Alignment Issues

| Principle | Status | Details |
|-----------|--------|---------|
| I. Specification-First Development | ✅ PASS | spec.md has prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, scope boundaries |
| II. Template-Driven Workflow | ❌ FAIL | plan.md missing required sections: Constitution Check, Technical Context, Complexity Tracking. Missing companion artifacts: research.md, data-model.md, contracts/, quickstart.md (C1–C4) |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear phase-based handoffs between specify → plan → tasks |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly required by FR-035 and SC-005; tasks include test creation (T069–T073) |
| V. Simplicity and DRY | ✅ PASS | YAGNI approach: hardcoded KNOWN_SECRETS constant, reuse of existing components (SettingsSection, DynamicDropdown, globalSettingsSchema) |

---

## Unmapped Tasks

All tasks (T001–T080) map to at least one requirement, user story, or cross-cutting concern. No orphan tasks detected.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 35 (FR-001 through FR-035) |
| Total Success Criteria | 10 (SC-001 through SC-010) |
| Total User Stories | 7 (US1–US7) |
| Total Tasks | 80 (T001–T080) |
| FR Coverage (FRs with ≥1 task) | **100%** (35/35) |
| SC with Validation Task | **70%** (7/10) — SC-001, SC-003, SC-007 lack explicit measurement |
| Edge Cases with Tasks | **75%** (6/8) — session expiry redirect, unconfigured admin ID missing |
| Ambiguity Count | 3 (U1, U2, A1) |
| Duplication Count | 2 (D1, D2) |
| Critical Issues Count | **4** (C1, C2, C3, C4) |
| High Issues Count | **3** (I1, I2, E1) |
| Medium Issues Count | **5** (E2, E3, E4, U1, U2, A1) |
| Low Issues Count | **4** (D1, D2, S1, S2) |

---

## Next Actions

### ⛔ CRITICAL issues require resolution before `/speckit.implement`

The 4 CRITICAL findings (C1–C4) are all constitution violations related to plan.md structure and missing companion artifacts. These **must** be addressed before proceeding to implementation:

1. **Run `/speckit.plan` with refinement** to add the missing Constitution Check, Technical Context, and Complexity Tracking sections to `plan.md`. Generate companion artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`).

2. **Fix `require_session` → `get_session_dep` references** (I1, A1) in spec.md assumptions and tasks.md T012. The correct import is `get_session_dep` from `solune/backend/src/api/auth.py`.

3. **Fix router registration location** (I2) in plan.md — change `main.py` to `api/__init__.py` in both the Project Structure tree and Phase 1 description.

4. **Add McpSettings.tsx and useMcpSettings.ts to US7 cleanup** (E1) in spec.md US7 acceptance scenarios and tasks.md Phase 9.

5. **Specify unsaved changes approach** (U1) in tasks.md T035 — recommend Shadcn `TabsContent forceMount` pattern.

### Suggested Commands

```bash
# Fix constitution compliance in plan.md:
/speckit.plan   # Re-run with refinement to add missing sections

# Or manually edit to fix HIGH issues:
# - spec.md line 223: "require_session" → "get_session_dep from src.api.auth"
# - tasks.md T012: "dependencies.py" → "auth.py", "require_session" → "get_session_dep"
# - plan.md lines 37, 79: "main.py" → "api/__init__.py"
# - tasks.md: Add T061.5 and T061.6 for McpSettings.tsx and useMcpSettings.ts deletion
```

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 7 issues (C1–C4, I1, I2, E1)? These edits would target specific lines in spec.md, plan.md, and tasks.md. *(No changes will be applied automatically — review and approval required.)*
