# Research: Code Quality & Technical Debt Overhaul

**Branch**: `033-code-quality-overhaul` | **Date**: 2026-03-10

## Research Tasks & Findings

### R-001: Structured JSON Logging — Best Practices for FastAPI

**Context**: FR-027/FR-028 require structured JSON logging backend-wide. The codebase already has `StructuredJsonFormatter` and `RequestIDFilter` in `logging_utils.py` but only 4 of ~45 backend files import from it.

**Decision**: Wire up the existing `StructuredJsonFormatter` from `logging_utils.py` as the root handler; no new library needed.

**Rationale**: The codebase already implements a `StructuredJsonFormatter` (JSON with timestamp, level, message, logger, request_id) and a `SanitizingFormatter` (redacts secrets). These are production-ready. The work is configuration, not implementation:
1. Set the JSON formatter as the root logging handler in `main.py` lifespan
2. Replace any remaining `print()` calls (research found 0 real ones — only 2 in string literals)
3. Ensure all `logger.info("message")` calls use `extra={}` for structured fields where context is available

**Alternatives Considered**:
- `python-json-logger` library — Rejected: duplicates existing `StructuredJsonFormatter`
- `structlog` — Rejected: heavy migration, incompatible with existing `logging.getLogger()` pattern used in 45+ files
- Custom middleware-only approach — Rejected: doesn't cover service-layer logs outside request context

### R-002: God Class Split — Incremental Extraction Without Facade

**Context**: FR-014 specifies incremental extraction without a facade — all callers of a given domain updated in the same PR as the extraction.

**Decision**: Extract in dependency order: identities (static, 0 callers of service) → rate_limit (internal only) → base_client (shared infrastructure) → branches → pull_requests → issues → projects.

**Rationale**: The extraction order is driven by dependency depth:
1. **`identities.py`** (bot detection) — Pure static functions, no dependency on service class. Extract first as warmup.
2. **`rate_limit.py`** (RateLimitManager) — Used internally by `_request_with_retry()`. Extract before base_client so base_client can inject it.
3. **`base_client.py`** — Shared `_graphql()`, `_rest()`, `_request_with_retry()`, ETag cache, request coalescing. All domain services inherit from this.
4. **`branches.py`** — Fewest callers (~5), lowest risk domain extraction.
5. **`pull_requests.py`** — Moderate callers (~8), some overlap with issues.
6. **`issues.py`** — Most callers (~15), highest risk domain extraction.
7. **`projects.py`** — Board/project methods, moderate callers (~10).

Each extraction is one commit: move methods + update all callers + update DI + run tests.

**Alternatives Considered**:
- Big-bang rewrite — Rejected by user (too risky for 5,338-line class with 83 methods)
- Facade pattern — Rejected by user (adds indirection layer that must be removed later)
- Strangler pattern (new callers use new service, old callers stay) — Rejected: creates confusing dual import paths

### R-003: Chat Storage Migration — dict to SQLite

**Context**: FR-012 requires replacing the in-memory `_messages` dict with persistent storage + automatic expiration. The codebase already uses `aiosqlite` for settings/session storage.

**Decision**: Create a `chat_messages` table in the existing SQLite database with TTL-based cleanup.

**Rationale**: The existing `aiosqlite` infrastructure provides connection management, migration patterns, and is already a dependency. The chat message store needs:
- Key: `(session_id, conversation_id)` composite
- Value: JSON-serialized message list
- TTL: configurable expiration (default 24h), enforced by periodic cleanup or lazy deletion on read
- Migration: backward-compatible — existing in-memory messages are lost on restart anyway (stateless)

Schema:
```sql
CREATE TABLE IF NOT EXISTS chat_messages (
    session_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    messages TEXT NOT NULL,  -- JSON array
    updated_at REAL NOT NULL,
    PRIMARY KEY (session_id, conversation_id)
);
CREATE INDEX idx_chat_messages_updated ON chat_messages (updated_at);
```

**Alternatives Considered**:
- Redis — Rejected: adds new infrastructure dependency (out of scope per spec)
- `BoundedDict` with LRU eviction — Rejected: already exists in utils.py but doesn't persist across restarts; still in-memory
- File-based JSON storage — Rejected: no concurrent access safety, no TTL mechanism

### R-004: Frontend Form State — react-hook-form + zod

**Context**: FR-021 requires declarative form state management to eliminate manual flatten/unflatten cycles in GlobalSettings.tsx.

**Decision**: Adopt `react-hook-form` + `zod` for the settings form refactoring.

**Rationale**: GlobalSettings.tsx currently manages 14 form fields with manual state spreading:
- `flattenSettings()` spreads nested config into flat state
- `unflattenSettings()` reconstructs nested config from flat state
- Each field change triggers a full re-render of all 14 fields

`react-hook-form` provides:
- Controlled/uncontrolled hybrid inputs (minimal re-renders)
- Nested object support via `useForm({ defaultValues: nestedConfig })` — eliminates flatten/unflatten
- Built-in `zod` resolver for schema validation

**Alternatives Considered**:
- `useReducer` only — Rejected: still requires manual flatten/unflatten for nested config
- Formik — Rejected: heavier bundle, less TypeScript integration than react-hook-form
- Keep current pattern but extract helpers — Rejected: still O(n) re-renders per keystroke

### R-005: Emoji State Detection → Typed Enum

**Context**: FR-011 requires replacing emoji-based state detection strings with a typed enumeration.

**Decision**: Create an `AgentStepState` enum mapping emoji patterns to typed states.

**Rationale**: recovery.py and agent_output.py use string matching like `"✅ Done"`, `"🔄 Active"`, `"⏳ Queued"` to detect agent step states from tracking table markdown. This is fragile (encoding issues, partial matches) and untestable. A typed enum with a `from_markdown()` classmethod centralizes the parsing:

```python
class AgentStepState(str, Enum):
    DONE = "done"
    ACTIVE = "active"
    QUEUED = "queued"
    ERROR = "error"
    SKIPPED = "skipped"

    @classmethod
    def from_markdown(cls, cell_text: str) -> "AgentStepState":
        """Parse tracking table cell text into typed state."""
        ...
```

**Alternatives Considered**:
- Keep strings but centralize in constants — Rejected: constants don't enforce exhaustive matching
- Pydantic model with validator — Rejected: unnecessary for a simple enum; adds serialization overhead
- Regex patterns — Rejected: still string-based, no type safety

### R-006: Polling Loop Data-Driven Steps

**Context**: FR-013 requires defining polling steps as a data structure rather than repeated inline conditional blocks.

**Decision**: Create a `PollStep` dataclass and iterate over a step list.

**Rationale**: `polling_loop.py` has 5 steps that each follow the same pattern: check rate limit → execute → handle error → log. The only differences are the function called, whether it's "expensive" (needs rate-limit budget), and the step name. A data-driven approach:

```python
@dataclass
class PollStep:
    name: str
    execute: Callable[..., Awaitable[None]]
    is_expensive: bool = False

POLL_STEPS: list[PollStep] = [
    PollStep("check_assignments", check_assignments),
    PollStep("post_agent_outputs", post_agent_outputs, is_expensive=True),
    PollStep("recover_stalled", recover_stalled, is_expensive=True),
    PollStep("cleanup_completed", cleanup_completed),
    PollStep("sync_board", sync_board),
]
```

**Alternatives Considered**:
- Chain of Responsibility pattern — Rejected: over-engineered for 5 fixed steps
- Plugin/registry pattern — Rejected: steps are known at compile time, no runtime extension needed

### R-007: Pyright Standard Mode — Impact Assessment

**Context**: FR-007 (via SC-007) and the session plan mention upgrading pyright from `basic` to `standard` mode.

**Decision**: Upgrade to `standard` mode in Phase 6 after all refactoring is complete.

**Rationale**: Upgrading before refactoring would add noise — hundreds of new type warnings in code that's about to be restructured. Do it last so warnings reflect the final codebase state. Expected new findings:
- Missing return type annotations on service methods (addressed in Phase 4 via FR-017)
- `Any` types in mock-heavy test code (excluded from pyright scope)
- GraphQL response dicts without type narrowing (addressed by new Pydantic response models)

**Alternatives Considered**:
- Upgrade first to guide refactoring — Rejected: would create a massive initial diff of type annotation fixes unrelated to the spec's goals
- Keep `basic` mode — Rejected: spec SC-007 requires zero new static analysis warnings; standard mode catches real bugs

### R-008: Test Mock `spec=` Parameter — Best Practice

**Context**: FR-024 requires `spec=` on mock constructors. The test suite has 5 mock factories in `helpers/mocks.py` + additional inline mocks.

**Decision**: Add `spec=` to all mock factories in conftest.py (after consolidation) and to high-value inline mocks in tests for refactored modules.

**Rationale**: `AsyncMock(spec=GitHubProjectsService)` ensures mock calls match the real class's method signatures. Without it, tests can pass with typos in method names or wrong argument counts. This is especially important after the God class split — callers must use the correct new service's method signatures.

**Alternatives Considered**:
- `autospec=True` — Rejected: too strict for async mocks (known issues with `__aenter__`/`__aexit__`)
- Type-checked mocks via pyright — Rejected: pyright doesn't validate mock call signatures even in standard mode
