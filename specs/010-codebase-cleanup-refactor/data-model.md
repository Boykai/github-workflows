# Data Model: Codebase Cleanup — Remove Dead Code, Backwards Compatibility & Stale Tests

**Feature**: `010-codebase-cleanup-refactor` | **Date**: 2026-02-28

> **Note**: This is a pure refactoring feature — no new data models, entities, or schema changes are introduced. This document catalogs the existing entities affected by cleanup and the nature of changes.

## Entities Affected by Cleanup

### Backend

#### 1. Token Encryption (Story 1 — Backwards Compatibility Removal)

**File**: `backend/src/services/encryption.py`

| Field/Logic | Current State | After Cleanup |
|-------------|---------------|---------------|
| Plaintext fallback (`gho_` prefix detection) | Active — handles legacy unencrypted tokens on decrypt | Evaluate: remove if all tokens migrated, retain with deprecation log if not |
| `decrypt()` method | Returns plaintext for `gho_` prefix, decrypts for others | Single path: decrypt only (if fallback removed) |

**Validation Rules**: If plaintext fallback is removed, any unencrypted token in the database will cause a decryption error. Verify via database audit that zero plaintext tokens exist before removal.

#### 2. Pipeline Legacy Paths (Story 1 — Evaluation)

**File**: `backend/src/services/copilot_polling/pipeline.py`

| Code Path | Current State | After Cleanup |
|-----------|---------------|---------------|
| "Legacy PR completion detection" | Active fallback for non-pipeline issues | Retain — serves active use case |
| "Legacy child PR merge handling" | Active for issues without agent pipelines | Retain — serves active use case |

**Decision**: These are not backwards compatibility shims — they handle the current case where issues exist without active pipelines. No removal needed; update comments to clarify they are "fallback" paths, not "legacy" paths.

#### 3. Silent Exception Handlers (Story 2 — Dead Code Adjacent)

**Files**: Multiple (see plan.md Source Code section)

| Location | Exception Type | Current Handler | After Cleanup |
|----------|---------------|-----------------|---------------|
| `api/settings.py:148` | `Exception` | `pass` | `logger.debug(...)` |
| `api/workflow.py:~82` | `ImportError` | `pass` | `logger.debug(...)` |
| `services/copilot_polling/agent_output.py:312` | `Exception` | `pass` | `logger.debug(...)` |
| `services/copilot_polling/pipeline.py:~280` | `Exception` | `pass` | `logger.debug(...)` |
| `services/signal_chat.py:~240` | `Exception` | `pass` | `logger.debug(...)` |
| `services/ai_agent.py:550,585` | `json.JSONDecodeError` | `pass` | `logger.debug(...)` |
| `services/model_fetcher.py:330` | `ValueError, TypeError` | `pass` | `logger.debug(...)` |
| `services/workflow_orchestrator/config.py:232` | `Exception` | `pass` | `logger.debug(...)` |
| `api/chat.py:286` | `RuntimeError` | `pass` | `logger.debug(...)` |

### Frontend

#### 4. Unused Type Exports (Story 2 — Dead Code)

**File**: `frontend/src/types/index.ts`

| Type | Lines | Status | Action |
|------|-------|--------|--------|
| `IssueLabel` | 162-184 | No imports found | Remove |
| `PipelineStateInfo` | 280-291 | No imports found | Remove |
| `AgentNotification` | 271-277 | No imports found | Remove |
| `SignalConnectionStatus` | ~447 | No imports found | Remove |
| `SignalNotificationMode` | ~449 | No imports found | Remove |
| `SignalLinkStatus` | ~451 | No imports found | Remove |

**Verification**: Run `grep -r "TypeName" frontend/src/` for each type before removal. Run `npm run type-check` after removal.

#### 5. Duplicated Logic in useAgentConfig (Story 3 — DRY)

**File**: `frontend/src/hooks/useAgentConfig.ts`

| Pattern | Lines | Occurrences | Consolidation |
|---------|-------|-------------|---------------|
| Agent order comparison loop | 108-120, 122-133 | 2 | Extract `hasAgentOrderChanged()` helper |

#### 6. Cache Pattern Duplication (Story 3 — DRY)

**Files**: `backend/src/api/board.py`, `backend/src/api/projects.py`, `backend/src/api/chat.py`

| Pattern | Occurrences | Consolidation Target |
|---------|-------------|---------------------|
| cache key → refresh check → get → return cached / fetch → set → return | 8+ | `cached_response()` utility in `cache.py` |

## State Transitions

No state machine changes. The cleanup is purely structural — existing state transitions in `workflow_orchestrator` and `copilot_polling` are preserved without modification.

## Relationships

No new entity relationships introduced. Existing relationships are preserved:
- Pipeline → Issue (retained, "legacy" comments updated)
- Token → Encryption (plaintext fallback evaluated for removal)
- API Handler → Cache (consolidated through shared utility)
