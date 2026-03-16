# Specification Analysis Report

**Feature**: Settings Page Refactor with Secrets (`048-settings-page-refactor`)
**Analyzed**: 2026-03-16
**Artifacts**: spec.md, plan.md, tasks.md
**Constitution**: v1.0.0 (Ratified 2026-01-30)

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution | CRITICAL | plan.md (entire file) | Plan is missing mandatory **Constitution Check** section. Constitution §Compliance Review: "All feature plan.md files MUST include a 'Constitution Check' section." Plan template also requires pre-research + post-design gates. | Add Constitution Check section evaluating compliance with all 5 principles before proceeding to implement. |
| C2 | Constitution | CRITICAL | specs/048-settings-page-refactor/ | Plan is missing mandatory **companion artifacts**: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`. Constitution §Phase-Based Execution requires Plan phase to generate these. Plan template §Project Structure mandates them. | Generate missing companion artifacts or add explicit justification for omission in a Complexity Tracking section. |
| C3 | Constitution | CRITICAL | plan.md (entire file) | Plan is missing mandatory **Complexity Tracking** section. Constitution Principle V: "complexity MUST be justified in the 'Complexity Tracking' section of plan.md." Plan template requires this section. | Add Complexity Tracking section (may contain "None identified" if no violations). |
| I1 | Inconsistency | HIGH | tasks.md:L52 (T012), spec.md:L223 | T012 references `require_session` from `solune/backend/src/api/dependencies.py` — **neither exists**. Actual auth dependency is `get_session_dep` from `src.api.auth`. Spec assumption (L223) also references non-existent `require_session`. | Update T012 to import `get_session_dep` from `solune/backend/src/api/auth`. Update spec assumption. |
| I2 | Inconsistency | HIGH | plan.md:L79 vs tasks.md:L61 (T018) | Plan says "Register secrets router in `solune/backend/src/main.py`". Tasks (T018) correctly say `solune/backend/src/api/__init__.py`. The actual codebase registers all routers in `api/__init__.py`, not `main.py` (which only mounts the aggregate router at `/api/v1`). | Correct plan.md L79 to reference `api/__init__.py`. |
| U1 | Underspecification | HIGH | spec.md:FR-034, tasks.md:Phase 9 | **Dead code not in cleanup scope**: `McpSettings.tsx` (449 lines) and `useMcpSettings.ts` (87 lines) are confirmed dead code — zero external imports in the entire codebase. Neither is listed in FR-034 for deletion nor in US7 cleanup tasks. | Add `McpSettings.tsx` and `useMcpSettings.ts` to FR-034 deletion list and add corresponding tasks T062.1/T062.2 in Phase 9. |
| I3 | Inconsistency | HIGH | plan.md:L79 vs parent issue §Phase 1 item 3 | Parent issue says "Register router in `solune/backend/src/main.py`" — same incorrect reference as plan.md. The plan propagated this error from the parent issue. | Fix both plan.md and note parent issue discrepancy. |
| A1 | Ambiguity | MEDIUM | plan.md:L122 | `pynacl` version listed as `latest` — no pinned version. Dependency resolution may produce different versions across environments. | Pin to specific version (e.g., `pynacl >= 1.5.0`) in plan and in T001. |
| U2 | Underspecification | MEDIUM | spec.md, tasks.md | **SC-007** (load time must not increase >10%) has **zero task coverage**. No task measures, benchmarks, or validates performance. | Add a task in Phase 10 for performance baseline comparison or downgrade SC-007 to aspirational. |
| U3 | Underspecification | MEDIUM | spec.md, tasks.md | **SC-008** (source file count decrease by ≥5) has **zero task coverage**. No task validates the file count delta after cleanup. | Add a validation task in Phase 10 or integrate count check into T080 manual verification. |
| A2 | Ambiguity | MEDIUM | spec.md (L146–L210) | Spec has no **Non-Functional Requirements** section. Performance constraint (SC-007: <10% load time increase), security constraints (NaCl encryption, no secret value exposure), and scalability considerations are scattered across success criteria and assumptions rather than structured as NFRs. | Add an explicit NFR section consolidating performance, security, and reliability requirements. |
| U4 | Underspecification | MEDIUM | spec.md Edge Cases, tasks.md | Edge case "empty secret value rejection" is specified in spec (L140) but **no task** explicitly implements empty-value validation for the Set Secret flow. T013 covers max-size validation only; T042-T043 focus on password UX. | Add explicit empty-value validation to T013 (Pydantic model: `value: str` with `min_length=1`) or T043 (frontend validation). |
| I4 | Inconsistency | MEDIUM | spec.md:L223, plan.md:L12, tasks.md:L52 | **Terminology drift**: `require_session` used in spec assumptions and plan, but actual codebase uses `get_session_dep`. Three artifacts reference the wrong name consistently, compounding the error. | Standardize to `get_session_dep` across all artifacts. |
| A3 | Ambiguity | MEDIUM | plan.md:L16 | `pynacl (NEW)` is the only new dependency but no security assessment or license compatibility check is mentioned. NaCl is a cryptography library that may have specific build requirements (`libsodium`). | Add note about `pynacl` build dependency on `libsodium` and license (Apache 2.0) compatibility. |
| U5 | Underspecification | MEDIUM | plan.md (entire file) | Plan is missing **Technical Context** section in template-prescribed format (language/version, storage, testing framework, constraints). Plan has "Tech Stack" (L14-18) but not structured per template. | Restructure Tech Stack into proper Technical Context format per plan template. |
| D1 | Duplication | LOW | spec.md:FR-026 vs FR-032 | FR-026 specifies `autocomplete="off"` for secret inputs; FR-032 also specifies `autocomplete="off"` as an accessibility requirement. Same attribute mandated by two different FRs. | Consolidate: FR-032 can reference FR-026 for `autocomplete` and add only `aria-label` as unique accessibility requirement. |
| U6 | Underspecification | LOW | spec.md Edge Cases, tasks.md | Edge case "session expires on Secrets tab" (L143) has no explicit task. Behavior (redirect to login, return to Secrets tab) is assumed to be handled by existing auth infrastructure but not verified. | Add verification step to T080 or accept as existing infrastructure behavior. |
| A4 | Ambiguity | LOW | spec.md:L222, tasks.md:T039 | Spec says "user's available repositories" for repo selector but doesn't specify the data source. T039 says "using existing `useProjects()` or `projectsApi.listProjects()` hook" — the "or" is ambiguous. | Clarify: decide on `useProjects()` as the canonical source and remove ambiguity. |
| U7 | Underspecification | LOW | tasks.md:Phase 8 (T059) | T059 says McpPresetsGallery should "call `useCheckSecrets()` hook" but doesn't specify which `owner/repo` to use. The Tools page may operate in a multi-repo context. | Clarify: T059 should specify using the currently selected project's owner/repo from the tools page context. |

---

## Coverage Summary

### Functional Requirements → Task Mapping

| Requirement | Has Task? | Task IDs | Notes |
|-------------|-----------|----------|-------|
| FR-001 (Tab interface) | ✅ | T031 | |
| FR-002 (Essential default) | ✅ | T031 | |
| FR-003 (URL hash update) | ✅ | T033 | |
| FR-004 (Direct URL nav) | ✅ | T032 | |
| FR-005 (Admin visibility) | ✅ | T034 | |
| FR-006 (Unsaved changes) | ✅ | T035 | |
| FR-007 (Per-section save) | ✅ | T051 | |
| FR-008 (Essential content) | ✅ | T028–T030 | |
| FR-009 (No Signal on Essential) | ✅ | T029 | |
| FR-010 (Preferences content) | ✅ | T049 | |
| FR-011 (Preferences per-section save) | ✅ | T051 | |
| FR-012 (Admin content) | ✅ | T053 | |
| FR-013 (Admin validation reuse) | ✅ | T054 | |
| FR-014 (Non-admin fallback) | ✅ | T032 | |
| FR-015 (List secrets endpoint) | ✅ | T007, T014 | |
| FR-016 (Create/update secret) | ✅ | T008, T009, T015 | |
| FR-017 (Delete secret) | ✅ | T010, T016 | |
| FR-018 (Auto-create environment) | ✅ | T006, T015 | |
| FR-019 (Secret name validation) | ✅ | T015 | |
| FR-020 (Secret value size limit) | ✅ | T013 | |
| FR-021 (Auth requirement) | ✅ | T012, T014–T017 | ⚠️ References wrong dependency name |
| FR-022 (Repo selector) | ✅ | T039 | |
| FR-023 (Known secrets section) | ✅ | T040, T041 | |
| FR-024 (Set/Update/Remove) | ✅ | T043, T044 | |
| FR-025 (Custom secret form) | ✅ | T045 | |
| FR-026 (Password inputs) | ✅ | T042 | |
| FR-027 (COPILOT_MCP_ warning) | ✅ | T045 | |
| FR-028 (Preset required_secrets) | ✅ | T057, T058 | |
| FR-029 (Check secrets endpoint) | ✅ | T011, T017 | |
| FR-030 (Tools page warning) | ✅ | T059 | |
| FR-031 (Tab panel roles) | ✅ | T036, T074 | |
| FR-032 (Secret input a11y) | ✅ | T042, T075 | Partially duplicates FR-026 |
| FR-033 (Focus on tab switch) | ✅ | T037 | |
| FR-034 (Delete components) | ✅ | T061–T066 | ⚠️ Missing McpSettings.tsx + useMcpSettings.ts |
| FR-035 (Update tests) | ✅ | T068, T073 | |

### Success Criteria → Task Mapping

| Criterion | Has Task? | Task IDs | Notes |
|-----------|-----------|----------|-------|
| SC-001 (2-click AI access) | ✅ | T028–T030 | Implicit via tab structure |
| SC-002 (100% settings accessible) | ✅ | T049–T056 | Implicit via tab consolidation |
| SC-003 (Secrets round-trip <60s) | ✅ | T038–T048 | Implicit, not timed |
| SC-004 (Admin hidden for non-admin) | ✅ | T034 | |
| SC-005 (No regressions) | ✅ | T077–T078, T080 | |
| SC-006 (URL hash 100% reliable) | ✅ | T032–T033 | |
| SC-007 (Load time <10% increase) | ❌ | — | No performance measurement task |
| SC-008 (≥5 fewer source files) | ❌ | — | No file count validation task |
| SC-009 (Preset warnings 100%) | ✅ | T059 | |
| SC-010 (Accessibility audit) | ✅ | T074–T076 | |

---

## Constitution Alignment Issues

| Principle | Status | Detail |
|-----------|--------|--------|
| I. Specification-First | ✅ PASS | spec.md has prioritized user stories, GWT acceptance scenarios, scope boundaries |
| II. Template-Driven Workflow | ❌ FAIL | plan.md missing Constitution Check, Complexity Tracking, Technical Context sections; missing companion artifacts (research.md, data-model.md, contracts/, quickstart.md) |
| III. Agent-Orchestrated Execution | ✅ PASS | Artifacts follow specify → plan → tasks → implement flow |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly required per FR-035 and spec verification steps; tasks include test phases |
| V. Simplicity and DRY | ⚠️ WARN | Complexity Tracking section missing from plan.md (required even if empty); pynacl dependency is justified but not documented in tracking |

---

## Unmapped Tasks

All 80 tasks (T001–T080) map to at least one functional requirement, user story, or cross-cutting concern. No orphan tasks found.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 35 (FR-001 through FR-035) |
| Total Tasks | 80 (T001 through T080) |
| FR Coverage % | **100%** (35/35 FRs have ≥1 task) |
| SC Coverage % | **80%** (8/10 SCs have ≥1 task; SC-007, SC-008 uncovered) |
| User Stories | 7 (US1–US7) |
| Phases | 10 |
| CRITICAL Issues | 3 (C1, C2, C3 — all constitution violations) |
| HIGH Issues | 4 (I1, I2, U1, I3) |
| MEDIUM Issues | 7 (A1, U2, U3, A2, U4, I4, A3, U5) |
| LOW Issues | 4 (D1, U6, A4, U7) |
| Total Findings | 18 |

---

## Next Actions

### ⛔ CRITICAL — Resolve Before `/speckit.implement`

1. **C1, C3, U5**: Run `/speckit.plan` with refinement to add missing **Constitution Check**, **Complexity Tracking**, and **Technical Context** sections to plan.md
2. **C2**: Generate companion artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) or add explicit justification in Complexity Tracking for their omission (e.g., "No novel data model — extends existing entities only")
3. **I1, I4**: Correct `require_session` → `get_session_dep` (from `src.api.auth`) and `api/dependencies.py` → `src.api.auth` across spec.md (L223), plan.md (if referenced), and tasks.md (T012)
4. **I2, I3**: Correct router registration location from `main.py` → `api/__init__.py` in plan.md (L79)

### ⚠️ HIGH — Strongly Recommended

5. **U1**: Add `McpSettings.tsx` and `useMcpSettings.ts` to FR-034 deletion list and add cleanup tasks in Phase 9
6. **A1**: Pin `pynacl` version in plan.md and T001

### 💡 MEDIUM — Improve Before Implementing

7. **U2, U3**: Add performance and file-count validation tasks to Phase 10 for SC-007 and SC-008
8. **U4**: Add empty-value validation to T013 Pydantic model (`min_length=1` on `SecretSetRequest.value`)
9. **A2**: Add Non-Functional Requirements section to spec.md
10. **A4**: Clarify repo selector data source in T039 (remove "or" ambiguity)

### ✅ LOW — Proceed At Discretion

11. **D1**: Consolidate duplicate `autocomplete="off"` between FR-026 and FR-032
12. **U6, U7**: Add minor clarifications to tasks for session expiry and multi-repo context

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top N issues? (These would not be applied automatically — user approval required before any editing commands are invoked.)
