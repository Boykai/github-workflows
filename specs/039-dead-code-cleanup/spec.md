# Spec 039: Dead Code Cleanup Inventory

**Date**: 2026-03-22
**Parent**: specs/001-code-quality-tech-debt
**Tools**: `ruff check --select F401,F811 src/` and `vulture src/ --min-confidence 80`

## Purpose

Auditable inventory of all dead code items identified by static analysis
tools, with dispositions for each item. This spec was announced in
CHANGELOG but the directory did not previously exist — this document
closes that gap.

## Static Analysis Results

### ruff check --select F401,F811 src/

**Result**: 0 findings — no unused imports (F401) or redefined-but-unused
variables (F811) detected.

### vulture src/ --min-confidence 80

| # | File | Line | Finding | Confidence | Disposition |
|---|------|------|---------|------------|-------------|
| 1 | src/api/tasks.py | 176 | unused variable `task_id` | 100% | Defer — used by FastAPI path parameter extraction; removing would break the endpoint |
| 2 | src/services/otel_setup.py | 27 | unused variable `parent_context` | 100% | Retain — intentional OpenTelemetry configuration pattern; variable is consumed by the tracing framework at runtime |
| 3 | src/services/otel_setup.py | 40 | unused variable `timeout_millis` | 100% | Retain — intentional OpenTelemetry exporter configuration; consumed by the OTLP exporter initialisation |
| 4 | src/services/otel_setup.py | 118 | unused variable `attributes` | 100% | Retain — OpenTelemetry span attributes dict; consumed by the span context at runtime |
| 5 | src/services/otel_setup.py | 121 | unused variable `attributes` | 100% | Retain — OpenTelemetry span attributes dict; same pattern as item 4 |

### Previously identified dead code (manual inspection)

| # | File | Lines | Finding | Disposition |
|---|------|-------|---------|-------------|
| 6 | src/services/cleanup_service.py | 640–649 (original) | Unreachable `branch_in_delete` inner block — `preserved_branch_names` and `branches_to_delete` are mutually exclusive by construction | **Removed** in this PR (Phase 5 Part 1) |

## Summary

- **Total items identified**: 6
- **Removed**: 1 (cleanup_service.py dead block — 9 LOC)
- **Deferred**: 1 (tasks.py — false positive, used by FastAPI)
- **Retained**: 4 (otel_setup.py — false positives, used by OpenTelemetry runtime)
- **ruff findings**: 0

All vulture findings (items 1–5) are false positives caused by
framework-level consumption patterns that vulture cannot trace. No
additional dead code sweep is warranted at this time.
