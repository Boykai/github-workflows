# Specification Analysis Report: Observability & Monitoring

**Feature**: 001-observability-monitoring
**Date**: 2026-03-22
**Artifacts Analyzed**: spec.md, plan.md, tasks.md, constitution.md, research.md, data-model.md, contracts/ (3 files), checklists/requirements.md

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | MEDIUM | plan.md:L82 vs plan.md:L253 | Project Structure section references `encryption_service.py` but the actual file is `encryption.py`. The Notes section (L253) already corrects this, creating an internal inconsistency within plan.md itself. | Update plan.md:L82 to `encryption.py` to match the Notes correction and the actual codebase. |
| U1 | Underspecification | MEDIUM | spec.md FR-010, tasks.md T004, config.py | `agent_timeout_alert_minutes` (default 15) is defined as a configurable threshold in FR-010 and added to config in T004, but no task implements agent timeout detection or alert dispatch. The config field will exist with no consuming code. | Either (a) add a task to wire agent timeout alerting, or (b) add a note in tasks.md explaining this is a forward-looking config reserved for future use, or (c) remove from FR-010 and T004 if not needed now. |
| C1 | Coverage | MEDIUM | spec.md US2 scenario 6, tasks.md Phase 4 | US2 acceptance scenario 6 says "configurable thresholds for...agent_timeout_alert_minutes" should be respected by "alerting behavior," but no task wires an `agent_timeout` alert type. Scenario references a threshold that has config but no dispatch logic. | Align scenario 6 with actual scope: either add agent_timeout dispatch task or narrow scenario 6 to cover only `pipeline_stall_alert_minutes` and `rate_limit_critical_threshold`. |
| U2 | Underspecification | MEDIUM | tasks.md T007, state.py:L31+L36 | T007 checks "polling task is alive" by inspecting "the asyncio.Task from state.py" but state.py has both `_polling_task` (L31, single task) and `_app_polling_tasks` (L36, dict of tasks). Contract says "polling task" singular. Ambiguous which reference(s) to inspect. | Clarify in T007 or contract that the check targets `_polling_task` (the main loop task), not individual app polling tasks. |
| A1 | Ambiguity | LOW | spec.md SC-003 | "zero measurable overhead" — the word "measurable" is not quantified. Research.md clarifies that OTel imports alone add ~15ms startup + ~5MB memory, but SC-003 itself lacks a concrete threshold. | Consider rephrasing to "zero additional imports, network calls, or memory allocation from tracing libraries" for testability. |
| D1 | Duplication | LOW | spec.md FR-012, FR-017 | FR-012 ("deployments without the flag incur zero import or runtime overhead") and FR-017 ("no tracing libraries MUST be imported and no tracing-related processing MUST occur") overlap. FR-012 states the principle; FR-017 restates with specificity. | Acceptable — FR-017 refines FR-012. No action needed unless consolidating for brevity. |
| U3 | Underspecification | LOW | tasks.md T008 | T008 says models go "in `health.py` (or co-located)" — the "(or co-located)" is vague about acceptable alternative locations. | Remove ambiguity: specify `health.py` as the definitive location, since the readiness models are tightly coupled to the endpoint. |
| U4 | Underspecification | LOW | tasks.md T019 | T019 says to implement X-Request-ID correlation "in `otel_setup.py` or middleware" — the "or" introduces implementation location ambiguity. Research Decision 7 specifies reading `request_id_var`, but where to set the span attribute is unclear. | Specify that correlation should be implemented in `otel_setup.py` as a SpanProcessor, consistent with OTel best practices and the module's responsibility. |
| I2 | Inconsistency | LOW | issue description vs codebase | Issue description references `main.py (L335 lifespan)` but the actual `lifespan()` function is at L317 in main.py. Line references in the issue drift from actual code. | No action needed — plan.md and tasks.md do not hardcode these line numbers. Issue description line refs are informational only. |

---

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 readiness-endpoint-200 | ✅ Yes | T007 | |
| FR-002 readiness-endpoint-503 | ✅ Yes | T007, T008 | |
| FR-003 db-write-check | ✅ Yes | T007 | INSERT+DELETE on scratch table |
| FR-004 polling-disabled-pass | ✅ Yes | T007 | |
| FR-005 health-unchanged | ✅ Yes | T009, T027 | Verification in T027 |
| FR-006 alert-dispatcher-interface | ✅ Yes | T005 | |
| FR-007 alert-cooldown | ✅ Yes | T005 | Per-type 15-min cooldown |
| FR-008 pipeline-stall-alert | ✅ Yes | T011 | Wired in recovery.py |
| FR-009 rate-limit-critical-alert | ✅ Yes | T012 | Wired in polling_loop.py |
| FR-010 configurable-thresholds | ⚠️ Partial | T003, T004 | Config added, but `agent_timeout_alert_minutes` has no dispatch logic (see U1/C1) |
| FR-011 webhook-delivery | ✅ Yes | T005 | Fire-and-forget with fallback |
| FR-012 opt-in-tracing | ✅ Yes | T006, T013 | OTEL_ENABLED gate |
| FR-013 auto-instrument | ✅ Yes | T006 | FastAPI, HTTPX, aiosqlite |
| FR-014 manual-spans | ✅ Yes | T014, T015, T016, T017 | Polling, recovery, resolve, encrypt |
| FR-015 custom-metrics | ✅ Yes | T018 | Gauges + histogram |
| FR-016 request-id-correlation | ✅ Yes | T019 | X-Request-ID in span attributes |
| FR-017 zero-overhead-disabled | ✅ Yes | T013, T026 | Conditional import + verification |
| FR-018 opt-in-error-tracking | ✅ Yes | T020 | Sentry DSN gate |
| FR-019 exception-enrichment | ✅ Yes | T021 | User/project/request context |
| FR-020 no-double-tracing | ✅ Yes | T020 | traces_sample_rate=0 |
| FR-021 error-tracking-noop | ✅ Yes | T020 | No init when DSN empty |
| FR-022 record-snapshots | ✅ Yes | T023 | SHOULD — optional |
| FR-023 history-endpoint | ✅ Yes | T024 | SHOULD — optional |
| FR-024 prune-snapshots | ✅ Yes | T023 | 24-hour retention |
| FR-025 trace-visualization | ✅ Yes | T022 | SHOULD — Jaeger in Compose profile |

---

## Constitution Alignment Issues

**No constitution violations detected.**

| Principle | Status | Verification |
|-----------|--------|-------------|
| I. Specification-First | ✅ PASS | spec.md includes 6 prioritized user stories (2×P1, 2×P2, 2×P3), Given-When-Then acceptance scenarios, edge cases, and scope boundaries. |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. |
| III. Agent-Orchestrated | ✅ PASS | Workflow followed: speckit.specify → speckit.plan → speckit.tasks → speckit.analyze. |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; correctly omitted from tasks.md per constitution. |
| V. Simplicity & DRY | ✅ PASS | Alert dispatcher uses simple in-memory cooldown; OTel/Sentry are opt-in; complexity tracked in plan.md. |
| Branch Naming | ✅ PASS | Feature uses `001-observability-monitoring` pattern. |
| Phase-Based Execution | ✅ PASS | Specify → Plan → Tasks → Analyze phases completed in order. |
| Independent Stories | ✅ PASS | All 6 user stories have independent test criteria and deliver standalone value. |

---

## Unmapped Tasks

All tasks map to at least one requirement or cross-cutting concern:

| Task | Mapping | Notes |
|------|---------|-------|
| T001 | Infrastructure | OTel dependencies — supports FR-012, FR-013, FR-014 |
| T002 | Infrastructure | Sentry dependency — supports FR-018 |
| T003 | Infrastructure | OTel/Sentry config — supports FR-012, FR-018 |
| T004 | Infrastructure | Alert config — supports FR-010 |
| T026 | Verification | Zero-overhead regression — validates FR-017, SC-003 |
| T027 | Verification | /health unchanged — validates FR-005 |
| T028 | Verification | Quickstart validation — end-to-end smoke test |

---

## Codebase Cross-Reference Validation

All file paths referenced in plan.md and tasks.md were verified against the actual codebase:

| Referenced Path | Exists? | Key Code Landmarks Verified |
|-----------------|---------|----------------------------|
| `solune/backend/src/config.py` | ✅ | Settings class with validation |
| `solune/backend/src/main.py` | ✅ | lifespan (L317), middleware (L442–492), exception handler (L495–520) |
| `solune/backend/src/api/health.py` | ✅ | Existing GET /health endpoint (143 lines) |
| `solune/backend/src/services/copilot_polling/polling_loop.py` | ✅ | Polling loop at L335 |
| `solune/backend/src/services/copilot_polling/recovery.py` | ✅ | recover_stalled_issues() at L358 |
| `solune/backend/src/utils.py` | ✅ | resolve_repository() at L204 |
| `solune/backend/src/services/encryption.py` | ✅ | EncryptionService with encrypt/decrypt |
| `solune/backend/src/middleware/request_id.py` | ✅ | request_id_var ContextVar at L29 |
| `solune/backend/src/logging_utils.py` | ✅ | Structured logging (304 lines) |
| `solune/backend/src/services/copilot_polling/state.py` | ✅ | _polling_task (L31), _app_polling_tasks (L36) |
| `solune/backend/src/services/github_projects/service.py` | ✅ | get_last_rate_limit() (L244), _extract_rate_limit_headers() (L253) |
| `docker-compose.yml` | ✅ | Services: backend, frontend, signal-api |
| `solune/backend/pyproject.toml` | ✅ | Current deps: FastAPI, HTTPX, aiosqlite, etc. |
| `solune/backend/src/services/alert_dispatcher.py` | ✅ Absent | Correctly not yet created (NEW file) |
| `solune/backend/src/services/otel_setup.py` | ✅ Absent | Correctly not yet created (NEW file) |
| `solune/backend/src/services/rate_limit_tracker.py` | ✅ Absent | Correctly not yet created (NEW file) |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 25 (21 MUST + 4 SHOULD) |
| Total User Stories | 6 (2×P1, 2×P2, 2×P3) |
| Total Tasks | 28 |
| Coverage % (requirements with ≥1 task) | 96% (24/25 fully covered, 1 partial) |
| Ambiguity Count | 1 |
| Duplication Count | 1 |
| Underspecification Count | 4 |
| Inconsistency Count | 2 |
| Coverage Gap Count | 1 |
| Critical Issues | 0 |
| High Issues | 0 |
| Medium Issues | 4 |
| Low Issues | 5 |

---

## Next Actions

No CRITICAL or HIGH issues were found. The artifacts are well-constructed and ready for implementation. The following improvements are recommended but not blocking:

1. **Resolve MEDIUM findings before `/speckit.implement`** (recommended):
   - **I1**: Fix the `encryption_service.py` → `encryption.py` path in plan.md Project Structure (L82) to match the Notes correction and codebase.
   - **U1/C1**: Decide on `agent_timeout_alert_minutes` — either add a dispatch task, document it as forward-looking config, or remove it from FR-010/T004.
   - **U2**: Clarify in T007 that the polling check targets `_polling_task` (main loop task, state.py:L31).

2. **Optional LOW improvements** (can proceed without):
   - **A1**: Tighten SC-003 wording for testability.
   - **U3/U4**: Remove "or" phrasing in T008 and T019 to specify definitive implementation locations.

3. **Proceed to implementation**: With 0 CRITICAL and 0 HIGH issues, the artifacts are safe to implement via `/speckit.implement`. Address MEDIUM findings first for maximum clarity.

---

## Remediation

Would you like me to suggest concrete remediation edits for the top 4 MEDIUM issues? (Edits will NOT be applied automatically — review and approval required before any modifications.)
