# Data Model: Codebase Cleanup — Reduce Technical Debt

**Feature**: `018-code-cleanup` | **Date**: 2026-03-05

## Overview

This feature performs internal cleanup only — **no data model changes are introduced**. No new entities, tables, fields, or relationships are created. No existing data model schemas are modified.

## Entities

### No New Entities

This is a cleanup/refactoring feature. All changes are limited to:

- Removing unused code (functions, classes, components, imports, variables)
- Consolidating duplicated logic into shared implementations
- Removing stale tests and test artifacts
- Removing unused dependencies and configuration entries

### Existing Entities — No Schema Changes

The following existing data model entities are **not modified** by this cleanup:

| Entity | Location | Status |
|--------|----------|--------|
| `agent_configs` table | `backend/src/migrations/007_agent_configs.sql` | Unchanged |
| `global_settings` table | `backend/src/migrations/001_initial_schema.sql` | Unchanged |
| `chore_templates` table | `backend/src/migrations/010_chores.sql` | Unchanged |
| `schema_version` table | `backend/src/services/database.py` | Unchanged |
| All Pydantic models | `backend/src/models/*.py` | Internal consolidation only — no field changes |
| All TypeScript types | `frontend/src/types/index.ts` | Internal consolidation only — no field changes |

## Consolidation Targets (Internal Only)

The following model-layer changes may occur as part of duplication consolidation (FR-008, FR-011), but they do not change any public API shapes:

### Potential: Chat Response Model Base Class

Three existing chat response models share a similar structure:

| Model | File | Fields |
|-------|------|--------|
| `ChatMessagesResponse` | `backend/src/models/chat.py` | reply, session info, completion flag |
| `ChoreChatResponse` | `backend/src/models/chores.py` | reply, conversation_id, template_ready |
| `AgentChatResponse` | `backend/src/models/agents.py` | reply, session_id, is_complete, preview |

**Consolidation approach**: If field alignment is confirmed, extract a shared `BaseChatFlowResponse` model. If fields differ meaningfully, leave as-is per Constitution Principle V ("Duplication is preferable to wrong abstraction").

**API impact**: None — response shapes remain identical to callers.

## Validation Rules

No changes to validation rules. All existing validation (Pydantic models, database constraints, frontend form validation) remains unchanged.

## State Transitions

No changes to state machines or lifecycle transitions. The cleanup does not modify any business logic flows.
