# Data Model: Codebase Cleanup

**Date**: 2026-03-02  
**Feature**: 002-codebase-cleanup

## Overview

This feature does not introduce any new entities, modify existing data models, or change any database schemas. It is a pure cleanup operation.

## Entities Affected

### Entities Removed (Dead Code)

| Entity | Module | Reason |
|--------|--------|--------|
| `PipelineAction` (dataclass) | `backend/src/services/agent_tracking.py` | Only used by dead function `determine_next_action()` |
| `UserPreferencesRow` (Pydantic model) | `backend/src/models/settings.py` | Never imported by production code; tests use raw dicts |
| `GlobalSettingsRow` (Pydantic model) | `backend/src/models/settings.py` | Same as above |
| `ProjectSettingsRow` (Pydantic model) | `backend/src/models/settings.py` | Same as above |

### Entities Preserved (No Changes)

All entities used by production code are preserved unchanged:

- All models in `backend/src/models/` excluding the 3 `*Row` models above
- All TypeScript types in `frontend/src/types/index.ts` that are actively imported
- All database schemas (SQLite tables accessed via aiosqlite)

### Types Removed (Frontend)

45 unused type exports will be removed from `frontend/src/types/index.ts`. These types are defined but never imported by any component, hook, or service. Full list in [research.md](research.md#frontend-dead-code).

## Relationships

No relationship changes. The cleanup only removes orphaned code — all remaining relationships between entities, services, and API endpoints are preserved.

## State Transitions

No state transition changes. All workflow states and pipeline states function identically after cleanup.

## Validation Rules

No validation rule changes. All Pydantic validators and TypeScript type guards remain unchanged.
