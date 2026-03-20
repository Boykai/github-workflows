# Specification Analysis Report

**Feature**: 054-activity-audit-trail — Activity Log / Audit Trail
**Artifacts Analyzed**: `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `contracts/activity-api.yaml`
**Constitution**: `.specify/memory/constitution.md` v1.0.0
**Date**: 2026-03-20

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Coverage Gap | **CRITICAL** | spec.md:L30,L41; tasks.md (all); contracts/activity-api.yaml (all) | **Date range filtering has zero coverage.** US2 narrative (L30) says "filter by… date range," acceptance scenario 4 (L41) requires date range filter, but: (a) no FR explicitly mandates date range filtering (FR-007 only covers event type), (b) no API contract parameter exists for date range, (c) no task implements it, (d) plan.md never mentions it. This is a spec acceptance scenario with no downstream traceability at all. | Either add FR, API parameter, and task for date range filtering, OR remove US2 scenario 4 and the "by date range" phrase from the US2 narrative. The current state guarantees an unimplemented acceptance criterion. |
| C2 | Coverage Gap | **CRITICAL** | spec.md:L167 (FR-022); data-model.md:L43-44; tasks.md:T008 | **`pipeline_stage` events are defined but never instrumented.** FR-022 explicitly requires "stage completions" to be logged. The data model defines `pipeline_stage` as an event type. T021 maps the Pipeline filter to `pipeline_run,pipeline_stage`. But NO task creates `pipeline_stage` events anywhere — T008 only covers run lifecycle in `api/pipelines.py`, and the stage completion path (likely in the orchestrator or pipeline executor) has no instrumentation task. | Add a task to instrument pipeline stage completion logging (likely in the orchestrator or pipeline execution service), creating events with `event_type="pipeline_stage"`. |
| C3 | Coverage Gap | **CRITICAL** | spec.md:L155 (FR-016), L93; data-model.md:L48; tasks.md:T030 (L262), T021 (L185) | **`agent_execution` events are defined but never instrumented.** FR-016 lists "agent executions" as high-signal notifications. US5 scenario 5 references them. The data model defines `agent_execution` as an event type. T030 queries for `agent_execution` events, and T021 maps the Agent filter to include `agent_execution`. But NO task creates events with `event_type="agent_execution"` — T011 only instruments agent CRUD. The notification bell and filter chip will reference a phantom event type. | Add a task to instrument agent execution logging (wherever agent tasks are executed in the backend), or remove `agent_execution` from FR-016 high-signal list and filter mappings if agent execution tracking is out of scope for v1. |
| I1 | Inconsistency | **HIGH** | contracts/activity-api.yaml:L69-125; tasks.md:T004 (L54-56); spec.md:L135 (FR-005), L142 (FR-009) | **Entity history endpoint missing `project_id` scoping.** The feed endpoint (`GET /activity`) requires `project_id`, but the entity history endpoint (`GET /activity/{entity_type}/{entity_id}`) has no `project_id` parameter in either the API contract or T004. The DB index `idx_activity_entity` on `(entity_type, entity_id)` also lacks `project_id`. This means entity history returns events across ALL projects — inconsistent with the project-scoped design stated in FR-005 and plan.md line 20. | Add `project_id` as a required query parameter on the entity history endpoint in the contract and T004, or document this as an intentional design choice (entity_ids may be globally unique). |
| I2 | Inconsistency | **HIGH** | tasks.md:T021 (L185); tasks.md:T008-T015 | **Filter mappings reference event types with zero producers.** T021 maps UI categories to API event_type values including `pipeline_stage` and `agent_execution`, but no instrumentation task creates events of these types (see C2, C3). Users who filter by "Pipeline" or "Agent" will see no results for these sub-types, making the filter silently incomplete. | Align T021 mappings with actually-instrumented event types, or add instrumentation tasks for the missing types. |
| U1 | Underspecification | **HIGH** | spec.md:L30-41 (US2); all downstream artifacts | **US2 date range filter has no measurable definition.** Even if date range filtering were implemented, the spec provides no detail: What UI control? Date picker? Preset ranges? How does it interact with event type filters (AND or OR)? What timezone? No FR anchors the behavior. | If keeping date range filtering, add a dedicated FR (e.g., FR-007b) with specific acceptance criteria, UI description, and API parameter definition. |
| A1 | Ambiguity | **MEDIUM** | spec.md:L21 (US1 scenario 2) | **"Within 30 seconds" polling mechanism unspecified in spec.** US1 scenario 2 says new events appear "within 30 seconds without manual refresh." The plan/tasks use `staleTime: 30_000` (30s polling), but the spec doesn't state the mechanism (polling vs. push). If a developer reads only the spec, "without manual refresh" could imply WebSockets. | Add a note in the spec or FR clarifying that v1 uses polling at 30s intervals, not real-time push. (Plan.md assumption on L185 covers this but the spec itself is ambiguous.) |
| A2 | Ambiguity | **MEDIUM** | data-model.md:L193-199; tasks.md:T030 (L263) | **Notification type mapping `pipeline_run → 'agent'` is semantically misleading.** The existing `Notification` type only supports `'agent' \| 'chore'` literal types. Pipeline events are mapped to `'agent'`, which is incorrect semantically. While documented in data-model.md, any developer reading the code will be confused by pipeline failure notifications typed as "agent." | Consider extending the `Notification` type union to include `'pipeline'` or `'system'` as valid types, or add a code comment explaining the mapping rationale. |
| U2 | Underspecification | **MEDIUM** | spec.md:L120 (Edge Case 6); tasks.md (all) | **Deleted entity handling has no task.** Edge case 6 states: "entity links should gracefully indicate that the entity no longer exists." No task addresses this UI behavior (e.g., showing "Entity deleted" badge or disabling the link). T017 (ActivityPage) doesn't mention deleted entity handling. | Add acceptance detail to T017 or a new task to handle the deleted-entity link gracefully in activity event rows. |
| U3 | Underspecification | **MEDIUM** | tasks.md:Phase 5 (T022-T023) | **Phase 5 (US3) contains only verification tasks, no implementation.** T022 says "Verify InfiniteScrollContainer integration" and T023 says "Verify cursor-based pagination consistency." The actual infinite scroll implementation is in T017 (Phase 3/US1). Phase 5 has no code to write — only checks. This could confuse implementers who expect each phase to produce deliverables. | Reframe T022/T023 as "validation checkpoints" rather than implementation tasks, or merge them into Phase 3 as part of T017/T004 with verification notes. |
| U4 | Underspecification | **MEDIUM** | spec.md (all); constitution.md:L24-29 | **spec.md has no dedicated "Scope" or "Out of Scope" section.** Constitution Principle I requires "Clear scope boundaries and out-of-scope declarations." The spec scatters exclusions in the Assumptions section (L187-189: chat messages, login events, retention policy excluded) rather than a structured scope section. | Add an explicit "## Scope" / "### Out of Scope" section consolidating the scope declarations from Assumptions. |
| U5 | Underspecification | **MEDIUM** | spec.md:SC-007 (L203); tasks.md:T037 (L313) | **Performance validation tasks don't cover all success criteria.** T037 validates feed query with EXPLAIN QUERY PLAN (SC-002/SC-003) but no task validates SC-007 (logging overhead <50ms), SC-006 (entity history <1s for 100 events), or SC-004 (filter response <1s). | Expand T037 or add tasks for validating the remaining performance success criteria. |
| D1 | Duplication | **LOW** | spec.md:FR-001/FR-022-027; tasks.md:T008-T015 | **FR-001 is a superset of FR-022 through FR-027.** FR-001 says "persist every significant user and system action… including pipeline runs, stage transitions, chore triggers, CRUD operations…" FR-022–FR-027 individually specify the same event types with additional detail. FR-001 is redundant with the union of FR-022–FR-027. | Keep FR-022–FR-027 (they have measurable detail schemas). Consider rephrasing FR-001 as a summary/meta-requirement with a forward reference to FR-022–FR-027. |
| D2 | Duplication | **LOW** | spec.md:L55 (US3 scenario 1); spec.md:L138 (FR-008) | **Page size default stated twice.** US3 scenario 1 says "only the most recent 50 events load initially." FR-008 says "default of 50 events per page." Consistent but redundant. | No action needed — consistency is fine. Noted for completeness. |
| A3 | Ambiguity | **LOW** | tasks.md:T012 (L121) | **App lifecycle events "started/completed" not defined as event types.** T012 says actions include "created/updated/deleted/started/completed" for apps, but uses `event_type="app_crud"`. "Started/completed" implies lifecycle events, not CRUD. The data model has no `app_lifecycle` event type. | Clarify whether app start/complete are CRUD-type events or need a separate event type (e.g., `app_lifecycle`), and align with the data model enums. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 (persist all events) | ✅ | T008–T015 | Superset requirement; covered by individual instrumentation tasks |
| FR-002 (event fields) | ✅ | T001, T002 | Migration + Pydantic models |
| FR-003 (timestamp ordering) | ✅ | T001, T004 | Migration default + ORDER BY |
| FR-004 (fire-and-forget) | ✅ | T003 | try/except wrapper, never raises |
| FR-005 (paginated feed) | ✅ | T004, T016 | API + hook |
| FR-006 (cursor pagination) | ✅ | T004, T023 | Compound cursor (created_at, id) |
| FR-007 (event type filtering) | ✅ | T004, T020, T021 | API param + filter chips |
| FR-008 (page size) | ✅ | T004, T022 | Default 50, max 100 |
| FR-009 (entity history) | ✅ | T004, T024 | Entity history endpoint + hook |
| FR-010 (entity detail views) | ✅ | T025–T029 | 5 entity types covered |
| FR-011 (Activity page) | ✅ | T017, T018, T019 | Page + route + nav link |
| FR-012 (event row display) | ✅ | T017 | Icons, summary, timestamp, link |
| FR-013 (expand detail) | ✅ | T017 | Inline expansion |
| FR-014 (empty state) | ✅ | T017, T020 | Generic + filtered empty state |
| FR-015 (infinite scroll) | ✅ | T017, T022 | InfiniteScrollContainer |
| FR-016 (notification bell) | ⚠️ | T030 | References `agent_execution` events that are never created (C3) |
| FR-017 (unread badge) | ✅ | T030 | localStorage tracking |
| FR-018 (mark as read) | ✅ | T030 | localStorage pattern |
| FR-019 (View all link) | ✅ | T031 | Link to /activity |
| FR-020 (pipeline run history) | ✅ | T032, T033, T034 | API + component + integration |
| FR-021 (stage breakdown) | ✅ | T033 | Expandable stage view |
| FR-022 (pipeline events) | ⚠️ | T008 | Run lifecycle covered; **stage completions NOT instrumented** (C2) |
| FR-023 (workflow transitions) | ✅ | T009 | Orchestrator instrumentation |
| FR-024 (chore triggers) | ✅ | T010 | Trigger + CRUD logging |
| FR-025 (CRUD events) | ✅ | T010–T013 | Chores, agents, apps, tools |
| FR-026 (webhook events) | ✅ | T014 | Webhook instrumentation |
| FR-027 (cleanup events) | ✅ | T015 | Cleanup start/complete |
| **US2 Scenario 4** (date range) | ❌ | — | **No FR, no API param, no task** (C1) |

---

## Constitution Alignment Issues

| Principle | Status | Detail |
|-----------|--------|--------|
| I. Specification-First Development | ⚠️ PARTIAL | Spec has prioritized user stories ✅, GWT scenarios ✅, but **no dedicated "Scope" / "Out of Scope" section** — scope declarations are scattered in Assumptions (U4). |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates. |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear agent handoffs with defined inputs/outputs. |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly marked optional in tasks.md header; regression checks included (T035–T036). |
| V. Simplicity and DRY | ✅ PASS | Single table, reuse of existing patterns, complexity tracking in plan.md. |

No CRITICAL constitution violations. U4 is a MEDIUM structural gap (content exists but not in a dedicated section).

---

## Unmapped Tasks

All 38 tasks (T001–T038) map to at least one requirement or user story. No orphan tasks detected.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 27 |
| Total User Stories | 6 |
| Total Success Criteria | 8 |
| Total Tasks | 38 |
| Coverage % (FRs with ≥1 task) | 93% (25/27 fully covered; FR-016 and FR-022 partially covered) |
| **Critical Issues** | **3** (C1: date range gap, C2: pipeline_stage uninstrumented, C3: agent_execution uninstrumented) |
| High Issues | 3 (I1: entity history scoping, I2: phantom filter types, U1: date range unspecified) |
| Medium Issues | 5 |
| Low Issues | 3 |
| Ambiguity Count | 3 |
| Duplication Count | 2 |
| Total Findings | 14 |

---

## Next Actions

### ⛔ CRITICAL — Resolve before `/speckit.implement`

1. **C1 — Date Range Filtering**: This is a **spec-level decision**. Either:
   - Run `/speckit.specify` with refinement to add FR-007b (date range filtering), then update the API contract and add a task, OR
   - Remove US2 acceptance scenario 4 and the "by date range" phrase from the US2 narrative to defer to a follow-up feature.

2. **C2 — Pipeline Stage Events**: Run `/speckit.tasks` refinement or manually add a task to instrument pipeline stage completion logging (likely in the pipeline orchestrator or stage executor service) with `event_type="pipeline_stage"`.

3. **C3 — Agent Execution Events**: Either:
   - Add a task to instrument agent execution lifecycle logging in the agent execution service, OR
   - Remove `agent_execution` from the FR-016 high-signal list, T030 query filter, and T021 filter mapping if agent execution tracking is out of scope for v1. Update data-model.md enums accordingly.

### ⚠️ RECOMMENDED — Improve before or during implementation

4. **I1 — Entity history project scoping**: Add `project_id` query parameter to the entity history API contract and T004, or document the intentional omission.
5. **I2 — Phantom filter types**: Align T021 event_type mappings with actually-instrumented event types once C2/C3 are resolved.
6. **U2 — Deleted entity handling**: Add deleted-entity link handling detail to T017 or create a new task.
7. **U4 — Scope section**: Add an explicit "## Scope" / "### Out of Scope" section to spec.md to satisfy Constitution Principle I fully.

### ✅ OPTIONAL — Can proceed without

8. **U3, U5, D1, D2, A1, A2, A3**: Low-to-medium improvements that won't block implementation. Address opportunistically.

---

**Would you like me to suggest concrete remediation edits for the top 3 critical issues?** (I will NOT apply them automatically — this analysis is read-only.)
