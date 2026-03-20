# Specification Analysis Report: Undo/Redo Support for Destructive Actions

**Feature**: 054-undoable-delete
**Date**: 2026-03-20
**Artifacts Analyzed**: spec.md, plan.md, tasks.md, constitution.md, contracts/useUndoableDelete.ts, data-model.md, quickstart.md, research.md
**Source Code Verified**: useAgents.ts, useChores.ts, useTools.ts, useApps.ts, usePipelineConfig.ts, AppLayout.tsx, AgentCard.tsx, ChoreCard.tsx, ToolsPanel.tsx, AppDetailView.tsx, useUnsavedPipelineGuard.ts

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| H1 | Inconsistency | HIGH | spec.md:FR-012–FR-015, plan.md:L20, tasks.md:T009–T010 | Spec defines 4 deletable entity types (agents, tools, chores, pipelines) with FR-012–FR-015. Plan and tasks include a 5th type (apps) via T009/T010 and `useApps.ts` in the project structure, but no corresponding functional requirement exists in spec.md. SC-003 also counts only 4 types. | Either add FR-016 for apps in spec.md (renumbering FR-016→FR-020 for cleanup/lifecycle) and update SC-003 to say "5 entity types," OR remove T009/T010 from tasks.md and useApps.ts from plan.md project structure. Recommend the former — apps are deletable in the codebase and should be covered. |
| H2 | Ambiguity | HIGH | tasks.md:T007, tasks.md:T008 | T007 states the undoable pattern "replaces the two-step dependency check flow" for tools, but T008 says to "retain the existing affected-agents dependency check as a pre-confirmation warning dialog." Additionally, the current `deleteTool({ toolId, confirm: false })` in ToolsPanel.tsx may already execute the deletion when no affected agents exist (returns `success: true`), which would bypass the undo pattern entirely for tools without dependencies. | Clarify the tool delete flow in T008: (1) Change the first API call to a dedicated dependency-check endpoint or ensure `confirm=false` only checks without deleting, OR (2) Skip the dependency check and always use the undoable force-delete (confirm=true), showing a generic confirmation dialog instead. Update T007 and T008 to be consistent. |
| H3 | Inconsistency | HIGH | tasks.md:T017 | T017 lists 5 files for "cannot be undone" text removal: AgentCard.tsx, ChoreCard.tsx, ToolsPanel.tsx, AppDetailView.tsx, useUnsavedPipelineGuard.ts. However, source code verification confirms only 3 files contain this text: **ChoreCard.tsx** (`This cannot be undone.`), **AppDetailView.tsx** (`This action cannot be undone.`), and **useUnsavedPipelineGuard.ts** (`This action cannot be undone.`). AgentCard.tsx and ToolsPanel.tsx do NOT contain "cannot be undone" language. | Remove AgentCard.tsx and ToolsPanel.tsx from T017's file list. Keep ChoreCard.tsx, AppDetailView.tsx, and useUnsavedPipelineGuard.ts. |
| M1 | Coverage Gap | MEDIUM | spec.md:FR-019, tasks.md (all tasks) | FR-019 requires displaying a message when undo fails because the item was already permanently deleted by another process. No task explicitly covers this scenario. T018 covers API delete failure after grace window, but the undo-after-concurrent-external-deletion is a distinct code path (restoring cache from snapshot for an item that no longer exists server-side). | Add a task or extend T018 to cover the FR-019 scenario: when undo restores from cache but the next `invalidateQueries` refetch reveals the item is gone, show an informational message rather than silently re-removing it. Alternatively, accept that this edge case is implicitly handled by eventual consistency (item reappears briefly then disappears on refetch) and document this as the intended behavior. |
| M2 | Coverage Gap | MEDIUM | spec.md:Edge Cases (L100), tasks.md (all tasks) | Spec edge case: "What happens when the grace window is active and the user tries to interact with the deleted item via another route (e.g., a direct link or search result)?" has no corresponding task. The item would be accessible from server data via a direct route even while pending deletion locally. | Add a task or note in T002 specifying behavior: pending items accessed via direct link should display normally (server data is untouched during grace window). Alternatively, document this as acceptable behavior since the deletion hasn't occurred server-side. |
| M3 | Underspecification | MEDIUM | tasks.md:T003, quickstart.md:Step 2 | Existing delete mutations invalidate additional query keys beyond the list key. For example, `useDeleteAgent` invalidates both `agentKeys.pending(projectId)` and `agentKeys.list(projectId)`. The undoable hook's `onDelete` callback calls `agentsApi.delete()` directly, bypassing the mutation, and only invalidates the single `queryKey` passed to it. Secondary invalidations (e.g., pending agents) would be missed. | Extend the `onDelete` callback in each entity wrapper (T003, T005, T007, T009) to also invalidate related query keys after the API call, OR add an `additionalQueryKeys` option to `UseUndoableDeleteOptions` for the hook to invalidate on success. |
| M4 | Inconsistency | MEDIUM | plan.md:L20, plan.md:L87 | Plan summary (L20) states "4 entity types (agents, tools, chores, pipelines)" but the project structure section (L74–L87) lists 5 hooks to modify, including `useApps.ts`. Internal inconsistency within plan.md. | Update plan summary to say "5 entity types" if apps are in scope, or remove useApps.ts from the project structure if not. Must align with H1 resolution. |
| M5 | Ambiguity | MEDIUM | spec.md:US3 Scenario 2, spec.md:US3 Scenario 1 | US3 acceptance scenarios use the phrase "reflow smoothly" and "without visual glitches" as acceptance criteria. These are subjective and not measurable. Only the "within 100ms" threshold is concrete. "Smoothly" cannot be tested in an automated fashion. | Replace "smoothly" with a concrete criterion (e.g., "without visible empty gaps or layout shift > 0 CLS") or mark these scenarios as manual-verification-only. |
| L1 | Inconsistency | LOW | data-model.md:L22, contracts/useUndoableDelete.ts | data-model.md's PendingDeletion entity includes a `createdAt` field (`number` — `Date.now()` timestamp). This field does not appear in the contract interface (`UseUndoableDeleteOptions`, `UndoableDeleteParams`, `PendingEntry`) or the quickstart reference implementation. | Either remove `createdAt` from data-model.md (simplest) or add it to the PendingEntry interface in the contract if it serves a purpose (e.g., diagnostics, timeout remaining calculation). |
| L2 | Coverage Gap | LOW | spec.md:Edge Cases (L98), tasks.md (all tasks) | Spec edge case: "What happens when the user's network disconnects during the grace window?" has no explicit task. Implicitly handled by T018's error path (API delete fails → restore + error toast), but not explicitly verified. | No action required — T018's error handling covers this implicitly. Optionally add a note to T019's validation scenarios. |
| L3 | Ambiguity | LOW | spec.md:FR-011 | FR-011 states toast notifications should "stack cleanly without obstructing critical UI elements." The term "critical UI elements" is not defined. With `visibleToasts={3}` in the existing Toaster config, sonner handles stacking, but the boundary of "obstruction" is subjective. | Accept as-is — sonner's built-in stacking behavior with the existing `visibleToasts={3}` config is sufficient. The existing Toaster position (`bottom-right`) minimizes obstruction. |

---

## Coverage Summary

### Requirements → Tasks Mapping

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (undo toast display) | ✅ | T002, T003, T004 | Covered by hook creation + agent integration |
| FR-002 (configurable grace window) | ✅ | T002 | `undoTimeoutMs` defaults to 5000 in hook options |
| FR-003 (undo cancels delete) | ✅ | T002 | Core hook behavior |
| FR-004 (grace window expiry deletes) | ✅ | T002 | setTimeout-based deferred deletion |
| FR-005 ("Restored" toast) | ✅ | T002 | Shown on successful undo |
| FR-006 (optimistic removal) | ✅ | T002, T013 | setQueryData removes item; T013 verifies data shapes |
| FR-007 (restore without reload) | ✅ | T002, T014 | Snapshot restoration via setQueryData |
| FR-008 (correct position on restore) | ✅ | T014 | Full snapshot restoration preserves sort/filter state |
| FR-009 (multiple concurrent deletions) | ✅ | T015 | pendingIds Set + pendingRef Map per entity |
| FR-010 (independent undo) | ✅ | T015 | Each entry in Map independent |
| FR-011 (clean toast stacking) | ✅ | T001 | Verification of existing Toaster config |
| FR-012 (agents) | ✅ | T003, T004 | Hook wrapper + component handler |
| FR-013 (tools) | ✅ | T007, T008 | Hook wrapper + component handler (see H2 re: flow) |
| FR-014 (chores) | ✅ | T005, T006 | Hook wrapper + component handler |
| FR-015 (pipelines) | ✅ | T011, T012 | Consumer-level integration via useUnsavedPipelineGuard |
| FR-016 (cancel on unmount) | ✅ | T016 | useEffect cleanup iterates Map |
| FR-017 (cleanup state) | ✅ | T002, T016 | Timer clearing + Map/Set cleanup |
| FR-018 (error notification) | ✅ | T018 | Restore cache + error toast on API failure |
| FR-019 (concurrent user conflict) | ❌ | — | No task covers undo-after-external-delete (see M1) |

### Unmapped Tasks (no corresponding requirement)

| Task ID | Description | Mapped Requirement | Notes |
|---------|-------------|-------------------|-------|
| T009 | useUndoableDeleteApp in useApps.ts | None | Apps not in spec FR-012–FR-015 (see H1) |
| T010 | Update AppDetailView.tsx delete handler | None | Apps not in spec (see H1) |
| T017 | Update "cannot be undone" dialog text | None (polish) | Cross-cutting improvement; no FR but supports UX consistency |
| T019 | Quickstart validation scenarios | None (validation) | End-to-end manual verification; cross-cutting |

---

## Constitution Alignment

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ⚠️ WARN | Apps entity (T009/T010) has tasks without spec coverage (H1). All other tasks trace to spec requirements. |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates. No custom sections. |
| III. Agent-Orchestrated | ✅ PASS | Clear phase handoffs: specify → plan → tasks. Artifacts are well-defined inputs/outputs. |
| IV. Test Optionality | ✅ PASS | No tests mandated. Tasks.md header explicitly acknowledges this per Constitution IV. T019 uses manual validation. |
| V. Simplicity and DRY | ✅ PASS | Single generic hook replaces 5 duplicate patterns. No new dependencies. No premature abstractions. |

**Constitution Note**: The apps entity gap (H1) is a WARN, not a CRITICAL violation. The spec covers the 4 entities mentioned in the original feature description. Apps were correctly identified during planning as an additional deletable entity in the codebase, and the plan/tasks extended scope accordingly. However, per Principle I, this scope extension should be reflected back in spec.md for traceability.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 19 |
| Total Tasks | 19 |
| Requirements with ≥1 Task | 18 / 19 |
| **Coverage %** | **94.7%** |
| User Stories | 5 (2×P1, 2×P2, 1×P3) |
| Success Criteria | 8 |
| Ambiguity Count | 3 (H2, M5, L3) |
| Duplication Count | 0 |
| Inconsistency Count | 4 (H1, H3, M4, L1) |
| Coverage Gap Count | 3 (M1, M2, L2) |
| Underspecification Count | 1 (M3) |
| **Critical Issues** | **0** |
| **High Issues** | **3** |
| **Medium Issues** | **5** |
| **Low Issues** | **3** |
| **Total Findings** | **11** |

---

## Next Actions

### Before `/speckit.implement`

The 3 HIGH issues should be resolved before implementation begins:

1. **H1 (Entity Scope)**: Run `/speckit.specify` with refinement to add apps as a 5th entity type (add FR for apps, update SC-003 count), OR remove T009/T010 from tasks.md if apps are intentionally out of scope.
2. **H2 (Tool Delete Flow)**: Manually edit tasks.md T007 and T008 to clarify whether the dependency check (`confirm=false`) is retained as a read-only check or replaced entirely by the undoable force-delete. Address the scenario where `confirm=false` already performs the deletion.
3. **H3 (T017 File List)**: Manually edit tasks.md T017 to remove AgentCard.tsx and ToolsPanel.tsx from the file list — only ChoreCard.tsx, AppDetailView.tsx, and useUnsavedPipelineGuard.ts need updating.

### Recommended but Non-Blocking

- **M1**: Extend T018 description to cover FR-019's concurrent user conflict scenario.
- **M3**: Add `additionalQueryKeys` option to hook design or extend onDelete callbacks to handle secondary invalidations (e.g., `agentKeys.pending()`).
- **M4**: Update plan.md summary to say "5 entity types" (after H1 resolution).
- **L1**: Remove `createdAt` from data-model.md PendingDeletion or add to contract if needed.

### Proceed If

All HIGH issues are addressed. MEDIUM issues may be resolved during implementation. LOW issues are informational and can be deferred.

---

## Remediation Offer

Would you like me to suggest concrete remediation edits for the top 3 HIGH issues? (Edits will NOT be applied automatically — approval required before any modifications.)
