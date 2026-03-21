# Specification Analysis Report: Optimistic Updates for Mutations

**Feature**: 001-optimistic-updates-mutations  
**Date**: 2026-03-21  
**Artifacts Analyzed**: spec.md, plan.md, tasks.md  
**Supporting Documents**: research.md, data-model.md, contracts/optimistic-cache-contract.md, quickstart.md, checklists/requirements.md  
**Constitution**: .specify/memory/constitution.md (v1.0.0)

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | CRITICAL | data-model.md:L56-80, types/index.ts:L1219-1232 | `McpToolConfig` placeholder construction in data-model.md uses non-existent fields (`command`, `args`, `env`, `enabled`). The actual type has `endpoint_url`, `config_content`, `sync_status`, `github_repo_target`, `is_active`. The optimistic placeholder template is **completely wrong** and will cause TypeScript compilation errors. | Rewrite McpToolConfig placeholder in data-model.md to match actual type. Use `McpToolConfigCreate` fields (`name`, `description`, `config_content`, `github_repo_target`) for user-provided data. Map remaining fields to sensible defaults (`sync_status: 'pending'`, `is_active: true`, etc.). |
| F2 | Inconsistency | CRITICAL | tasks.md:T003 (L79-83), data-model.md:L56-80 | Task T003 instructs constructing optimistic `McpToolConfig` with `command`/`description`/`enabled` fields that don't exist on the actual type. Implementation will fail at compile time. | Update T003 to reference actual `McpToolConfig` fields and `McpToolConfigCreate` input type. |
| F3 | Inconsistency | HIGH | tasks.md:T001 (L42-48), hooks/useAgents.ts:L64-76 | T001 targets `agentKeys.list(projectId)` for the create agent optimistic update, but the existing `useCreateAgent.onSuccess` invalidates `agentKeys.pending(projectId)`. New agents go to the **pending** list, not the active agents list. The optimistic placeholder should target the pending cache. | Clarify whether optimistic create should target `pending` or `list` cache. If agents first appear in pending, T001 must use `agentKeys.pending(projectId)` instead of `agentKeys.list(projectId)`. |
| F4 | Inconsistency | HIGH | data-model.md:L10-47, services/api.ts:L865-882 | `AgentConfig` data model is inaccurate: (a) lists `updated_at: string (ISO) Required` but actual type has NO `updated_at` field; (b) shows `created_at: string (ISO) Required` but actual type is `created_at: string | null`; (c) omits fields `slug`, `github_issue_number`, `github_pr_number`, `branch_name`; (d) shows `status_column: string` but actual type is `string | null`. Placeholder construction will produce incomplete objects. | Update AgentConfig data model to match actual type. Add missing fields with appropriate defaults (`slug: ''`, `github_issue_number: null`, `github_pr_number: null`, `branch_name: null`). Fix nullability of `created_at` and `status_column`. |
| F5 | Inconsistency | HIGH | research.md:L109 (Task 6), types/index.ts:L1248-1251 | Research states tools cache shape is `{ tools: McpToolConfig[] }` but actual type `McpToolConfigListResponse` is `{ tools: McpToolConfig[]; count: number }`. The `count` field must be preserved/updated in optimistic mutations to avoid UI inconsistencies where a count display disagrees with the visible list. | Update data-model.md and contracts to reflect `McpToolConfigListResponse = { tools: McpToolConfig[]; count: number }`. Task T003 onMutate must increment `count` on create. |
| F6 | Ambiguity | HIGH | spec.md:L42-54 (US3), tasks.md:T003 | Spec and tasks refer to "tool upload" and `uploadTool`, but the actual mutation is `toolsApi.create()` accepting a `McpToolConfigCreate` object (name, description, config_content, github_repo_target) — not a file upload. The term "upload" implies file handling (FormData, progress indicators) which is not what happens. This may mislead implementers into adding file upload semantics. | Standardize terminology to "tool creation" or "tool registration". Update spec US3 title, tasks T003 description, and quickstart to use `create` terminology matching the codebase. |
| F7 | Underspecification | MEDIUM | tasks.md:T001-T002, hooks/useAgents.ts:L20-24 | Tasks T001-T002 reference both flat and paginated keys but do not address the **pending** vs **list** key distinction. Agents have TWO separate query keys: `agentKeys.list(projectId)` (active agents) and `agentKeys.pending(projectId)` (pending agents). It's unclear which cache(s) the optimistic create/delete should target. | Explicitly specify whether create targets pending cache, list cache, or both. Specify whether delete targets list, pending, or both. |
| F8 | Underspecification | MEDIUM | spec.md:L105 (FR-001), tasks.md:T001 | FR-001 says "display newly created agents in the agents list" but doesn't define whether "agents list" means the active list, pending list, or both. The actual codebase has separate list views. | Clarify FR-001 to specify which list view(s) should reflect the optimistic agent. |
| F9 | Coverage Gap | MEDIUM | tasks.md (all phases), spec.md:L93-99 | Spec defines 7 edge cases (L93-99) but none have explicit task coverage. T008 (edge case guards) addresses some implicitly (empty cache, rapid mutations, missing projectId) but others are unaddressed: (a) mutation while list is still loading initial data; (b) navigate away before server responds; (c) server response significantly differs from placeholder; (d) session expired/network disconnected; (e) deleting last entity on paginated page; (f) optimistic create triggers new page needed. | Either add edge case validation subtasks to T008 or explicitly declare which edge cases are out of scope for the initial implementation. |
| F10 | Inconsistency | MEDIUM | tasks.md:T002 (L62), hooks/useAgents.ts:L95-113 | T002 says `useDeleteAgent` has "no onMutate" but the existing hook already has `onError` with `toast.error`. T002 only mentions adding `onMutate`, `onError`, and `onSettled` but doesn't acknowledge the existing `onError` — implementers might accidentally duplicate or conflict with it. | Note in T002 that `useDeleteAgent` already has `onError` with toast.error. The task should extend/replace the existing `onError` to include snapshot rollback while preserving the error toast. |
| F11 | Inconsistency | MEDIUM | tasks.md:T001 (L46), hooks/useAgents.ts:L64-76 | T001 says `useCreateAgent` has "no onMutate" (correct) but doesn't acknowledge the existing `onError` and `onSuccess` handlers. These must be preserved or merged with the new lifecycle callbacks. Implementer might overwrite them. | Note in T001 that existing `onSuccess` (toast + invalidation) and `onError` (toast) handlers must be preserved. The new `onMutate` and `onSettled` are additions; `onError` should be extended to add rollback. |
| F12 | Ambiguity | MEDIUM | spec.md:L114 (FR-010) | FR-010: "System MUST preserve scroll position and visible page state when optimistic updates are applied to paginated lists." No task addresses scroll position preservation. TanStack Query's `setQueryData` doesn't inherently guarantee this — it depends on React reconciliation and key stability. | Either add a task to verify scroll position preservation or document that TanStack Query's in-place cache update naturally preserves scroll position (making FR-010 implicitly satisfied). |
| F13 | Underspecification | MEDIUM | data-model.md:L86-115, types/apps.ts:L64-75 | Project placeholder uses `data.owner` for `owner_login` but `CreateProjectRequest` also has optional `repo_owner` and `repo_name` fields. These aren't mentioned in the data model. More importantly, the response (`CreateProjectResponse`) returns `project_id`, `project_number`, `project_url` — but the optimistic placeholder sets `url: ''`. The reconciliation on `onSettled` will fix this via invalidation, but the intermediate state has an empty URL. | Document that the optimistic Project placeholder will have an empty `url` and `owner_id` until server reconciliation. This is acceptable behavior but should be documented. |
| F14 | Duplication | LOW | spec.md:L106 (FR-006), spec.md:L112 (FR-012) | FR-006 ("revert list on failed mutation") and FR-012 ("display error notifications for failed mutations") partially overlap with acceptance scenario 3 in each user story (US1-US4), which all specify revert + error notification on failure. The FRs consolidate what the stories express individually. | Not blocking — the duplication is intentional (FRs generalize story-specific criteria). No action needed. |
| F15 | Inconsistency | LOW | quickstart.md:L26 (line numbers), hooks/useAgents.ts actual lines | Quickstart says `useCreateAgent` at "line ~64" and `useDeleteAgent` at "line ~95". Actual lines: useCreateAgent at L64-76, useDeleteAgent at L95-113. These are approximately correct but fragile — any code change will invalidate them. | Line numbers in quickstart are acceptable as approximate references. No action needed. |
| F16 | Ambiguity | LOW | spec.md:L138 (SC-001) | SC-001 requires "entity list updates within 100 milliseconds of user action". This is a client-side synchronous cache update via `setQueryData` which executes in microseconds. The 100ms threshold is trivially met and not meaningfully measurable. | Consider removing or rewording the 100ms criterion. "Immediately upon user action, before server response" is more precise and testable. |
| F17 | Inconsistency | LOW | tasks.md:T007 (L146-153), tasks.md:T005 (L118-128) | T007 (tool delete paginated) is listed without [P] marker but T005 and T006 are marked [P]. T007's dependency note correctly explains it depends on T003, but the missing [P] is inconsistent with the notation system — tasks without [P] are sequential dependencies, but this one is a file-level dependency, not a phase-level one. | Minor notational inconsistency. T007 correctly lacks [P] because it shares a file with T003. No action needed. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001: Agent create instant feedback | ✅ | T001 | ⚠️ May need to target pending cache instead of list cache (see F3) |
| FR-002: Agent delete instant feedback | ✅ | T002 | ⚠️ Same pending vs list ambiguity (see F7) |
| FR-003: Tool create instant feedback | ✅ | T003 | ⚠️ Placeholder uses wrong fields (see F1, F2) |
| FR-004: Tool error toast | ✅ | T003 | Explicitly called out in T003 |
| FR-005: Project create instant feedback | ✅ | T004 | ✅ Clean — no issues |
| FR-006: Revert on failure | ✅ | T001-T004 (onError) | Each task includes onError with rollback |
| FR-007: Reconcile with server data | ✅ | T001-T004 (onSettled) | Each task includes onSettled with invalidation |
| FR-008: Paginated cache updates | ✅ | T001-T007 | T001-T004 include paginated handling; T005-T007 fix existing hooks |
| FR-009: No duplicates after reconciliation | ⚠️ Implicit | T001-T007 (onSettled) | Covered by invalidation pattern, not explicitly tested |
| FR-010: Preserve scroll position | ❌ | None | No task explicitly addresses scroll position (see F12) |
| FR-011: Rapid sequential mutations | ⚠️ Implicit | T008 | T008 mentions "independent snapshots" but lacks specific validation steps |
| FR-012: Error notifications for all mutations | ✅ | T001-T004 (onError) | Each task includes toast.error |

---

## Constitution Alignment Issues

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md has prioritized stories, Given-When-Then scenarios, edge cases |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Clear single-purpose agent outputs |
| IV. Test Optionality | ✅ PASS | Tests explicitly omitted per constitution; noted in tasks.md |
| V. Simplicity and DRY | ✅ PASS | Reuses existing patterns; no premature abstraction |

No constitution violations detected.

---

## Unmapped Tasks

All tasks (T001-T009) map to at least one requirement or user story. No orphaned tasks.

---

## Metrics

| Metric | Count |
|--------|-------|
| Total Requirements (FR) | 12 |
| Total Tasks | 9 |
| Coverage % (FRs with ≥1 task) | 92% (11/12) |
| Ambiguity Count | 3 (F6, F12, F16) |
| Duplication Count | 1 (F14) |
| Critical Issues Count | 2 (F1, F2) |
| High Issues Count | 4 (F3, F4, F5, F6) |
| Medium Issues Count | 5 (F7, F8, F9, F10, F11) |
| Low Issues Count | 4 (F14, F15, F16, F17) |
| Total Findings | 17 |

---

## Next Actions

### CRITICAL Issues — Resolve Before `/speckit.implement`

1. **F1 + F2 (McpToolConfig type mismatch)**: The optimistic placeholder for tools will **fail at compile time**. Run `/speckit.plan` to regenerate `data-model.md` with correct `McpToolConfig` fields, then update `tasks.md` T003 accordingly. Alternatively, manually edit `data-model.md` and `tasks.md` to align with the actual `McpToolConfig` type (`endpoint_url`, `config_content`, `sync_status`, `github_repo_target`, `is_active`, `synced_at`, `sync_error`) and `McpToolConfigCreate` input type (`name`, `description`, `config_content`, `github_repo_target`).

### HIGH Issues — Strongly Recommend Resolving

2. **F3 (Agent create targets wrong cache key)**: Clarify whether `useCreateAgent` optimistic update should target `agentKeys.pending(projectId)` (where new agents actually appear) or `agentKeys.list(projectId)` (the active agents list). Update T001 accordingly.

3. **F4 (AgentConfig data model inaccurate)**: Update data-model.md AgentConfig to include missing fields (`slug`, `github_issue_number`, `github_pr_number`, `branch_name`) and fix nullability (`created_at: string | null`, `status_column: string | null`).

4. **F5 (Tools cache missing `count` field)**: Update data-model.md and T003 to include `count` in the wrapper object shape.

5. **F6 (Misleading "upload" terminology)**: Consider standardizing to "create" terminology to match the codebase API (`toolsApi.create()`).

### MEDIUM/LOW Issues — Can Proceed, Improvements Suggested

6. **F9 (Edge case coverage)**: Explicitly declare which of the 7 spec edge cases are deferred vs addressed by T008.
7. **F10-F11 (Existing handler acknowledgment)**: Note in T001/T002 that existing `onError`/`onSuccess` handlers must be preserved.
8. **F12 (Scroll position)**: Document whether TanStack Query's in-place update satisfies FR-010 or if additional work is needed.

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 6 issues (F1-F6)? These edits would target `data-model.md`, `tasks.md`, and `contracts/optimistic-cache-contract.md` to align with the actual codebase types. (Edits will NOT be applied automatically — you must explicitly approve before any follow-up editing commands are invoked.)
