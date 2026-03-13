# Data Model: Codebase Modernization & Technical Debt Reduction

**Branch**: `038-code-quality-overhaul` | **Date**: 2026-03-12
**Phase**: 1 — Design & Contracts

## Entities

### 1. ChatMessage (Persistence Layer)

**Source**: `services/chat_store.py` → `chat_messages` table (migration 012)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | SQLite rowid |
| session_id | TEXT | NOT NULL, INDEXED | Links messages to user session |
| sender | TEXT | NOT NULL | "user" or "assistant" (maps to `SenderType` enum) |
| content | TEXT | NOT NULL | Message body (plaintext or markdown) |
| timestamp | TEXT | NOT NULL | ISO 8601 UTC timestamp |
| metadata | TEXT | NULLABLE | JSON blob for command context, attachments, etc. |

**Relationships**: Belongs to a session (1:N session → messages). No FK constraint (session is ephemeral).

**State Transitions**: 
- Created → Persisted (on `save_message()`)
- Persisted → Deleted (on `clear_messages()` per session)

---

### 2. ChatProposal (Persistence Layer)

**Source**: `services/chat_store.py` → `chat_proposals` table (migration 012)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | UUID string (proposal_id) |
| session_id | TEXT | NOT NULL, INDEXED | Links proposal to session |
| proposal_type | TEXT | NOT NULL | "status_change", "task_create", etc. |
| payload | TEXT | NOT NULL | JSON blob with action details |
| status | TEXT | NOT NULL, DEFAULT 'pending' | pending → confirmed \| cancelled |
| created_at | TEXT | NOT NULL | ISO 8601 UTC timestamp |
| resolved_at | TEXT | NULLABLE | Timestamp when confirmed/cancelled |

**Relationships**: Belongs to a session. References tasks/issues via payload content (soft reference).

**State Transitions**:
```
pending → confirmed (user accepts)
pending → cancelled (user rejects)
```

**Validation Rules**:
- `proposal_type` must be a known type from the command handler
- `payload` must be valid JSON
- `status` transitions are one-way (confirmed/cancelled are terminal)

---

### 3. ChatRecommendation (Persistence Layer)

**Source**: `services/chat_store.py` → `chat_recommendations` table (migration 012)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | UUID string |
| session_id | TEXT | NOT NULL, INDEXED | Links to session |
| items | TEXT | NOT NULL | JSON array of recommended tasks/issues |
| status | TEXT | NOT NULL, DEFAULT 'pending' | pending → accepted \| dismissed |
| context | TEXT | NULLABLE | JSON blob with generation context |
| created_at | TEXT | NOT NULL | ISO 8601 UTC timestamp |

**Relationships**: Belongs to a session. Items reference GitHub issues/tasks (soft reference via owner/repo/number).

**State Transitions**:
```
pending → accepted (user selects items to create)
pending → dismissed (user declines)
```

---

### 4. PipelineConfiguration (Frontend State)

**Source**: `frontend/src/hooks/usePipelineConfig.ts` → TanStack Query cache

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | number | Required | Pipeline config ID from backend |
| name | string | Required | User-defined pipeline name |
| project_id | number | Required | Associated project |
| stages | Stage[] | Required | Ordered list of pipeline stages |
| agent_assignments | Record<string, string> | Required | Stage → agent slug mapping |
| is_active | boolean | Required | Whether pipeline is enabled |
| created_at | string | Required | ISO 8601 timestamp |
| updated_at | string | Required | ISO 8601 timestamp |

**Frontend State Decomposition** (post-refactor):
- **Orchestration** (`usePipelineOrchestration`): loading state, save triggers, error state
- **CRUD** (`usePipelineCrud`): create/read/update/delete via TanStack Query mutations
- **Dirty State** (`usePipelineDirtyState`): tracks unsaved changes, comparison with server state

---

### 5. GeneratedTypeContract (Build Artifact)

**Source**: `frontend/src/types/generated.ts` (output of `openapi-typescript`)

Not a runtime entity — a build-time artifact generated from the backend's OpenAPI schema.

| Aspect | Value |
|--------|-------|
| Input | `GET /openapi.json` from FastAPI backend |
| Output | `frontend/src/types/generated.ts` |
| Tool | `openapi-typescript` (npm) |
| Trigger | Manual via `scripts/generate-types.sh`, enforced by pre-commit hook |
| Contents | TypeScript interfaces for all Pydantic response/request models |

---

### 6. SharedConstants (Build Artifact)

**Source**: `frontend/src/constants/generated.ts` (output of generation script)

Not a runtime entity — a build-time artifact generated from `backend/src/constants.py`.

| Aspect | Value |
|--------|-------|
| Input | `backend/src/constants.py` exported constants |
| Output | `frontend/src/constants/generated.ts` |
| Tool | Custom Python script (reads constants, writes TS) |
| Trigger | Part of `scripts/generate-types.sh` pipeline |
| Contents | TypeScript `const` declarations for status names, agent slugs, pipeline defaults |

---

### 7. FrontendErrorReport (API Payload)

**Source**: New `POST /api/v1/errors` endpoint

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| message | string | Required, max 2000 chars | Error message |
| stack | string | Optional, max 10000 chars | Stack trace |
| url | string | Required | Page URL where error occurred |
| timestamp | string | Required | ISO 8601 UTC timestamp |
| user_agent | string | Optional | Browser user agent |

**Validation Rules**:
- `message` and `url` are required
- Endpoint rate-limited to prevent abuse
- No persistence — logged at ERROR level then discarded
- No sensitive data expected (frontend errors are client-side)

## Entity Relationship Diagram

```
Session (ephemeral)
├── 1:N → ChatMessage (persisted in chat_messages)
├── 1:N → ChatProposal (persisted in chat_proposals)
│            └── pending → confirmed | cancelled
└── 1:N → ChatRecommendation (persisted in chat_recommendations)
              └── pending → accepted | dismissed

Project
└── 1:N → PipelineConfiguration (persisted in pipeline_configs)
              └── Frontend manages via 3 decomposed hooks

Build Pipeline
├── OpenAPI Schema → GeneratedTypeContract (types/generated.ts)
└── constants.py → SharedConstants (constants/generated.ts)

Frontend Error → POST /api/v1/errors → Server-side log (no persistence)
```
