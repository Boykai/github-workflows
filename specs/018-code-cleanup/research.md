# Research: Codebase Cleanup — Reduce Technical Debt

**Feature**: `018-code-cleanup` | **Date**: 2026-03-05

## Research Tasks

### R1: Backwards-Compatibility Shims Audit

**Decision**: Audit identified several backwards-compatibility patterns. Most are still necessary (serving active transitions), but some can be safely removed after confirming no active callers depend on the old code path.

**Rationale**: Each shim must be individually assessed — removing a shim that still has callers would break functionality, while keeping unnecessary shims adds maintenance burden and cognitive load.

**Findings**:

1. **Legacy plaintext token fallback** (`backend/src/services/encryption.py:62-88`): The `_is_plaintext_token()` function and fallback logic in `decrypt_token()` handles pre-encryption plaintext GitHub tokens (`gho_`, `ghp_`, etc.). This is a classic migration-period shim. **Action**: Verify whether any tokens in storage are still plaintext; if all tokens have been encrypted, remove the fallback.

2. **Model re-exports for import compatibility** (`backend/src/models/chat.py:18-40`): After refactoring Agent, Recommendation, and Workflow models into separate files, `chat.py` re-exports them with `# noqa: F401` to avoid breaking existing `from src.models.chat import Agent` imports. **Action**: Audit all imports across the codebase; if all callers use the new import paths, remove the re-exports.

3. **Service module re-exports** (`backend/src/services/workflow_orchestrator/__init__.py:10-11`, `backend/src/services/copilot_polling/__init__.py:193`): Re-exports for backwards-compatible import paths. **Action**: Verify whether callers use the package-level imports or the direct submodule imports, and consolidate.

4. **Dynamic agent slug extraction with `hasattr` fallbacks** (`backend/src/services/agent_tracking.py:105`, `backend/src/services/workflow_orchestrator/config.py:268`, `orchestrator.py:711`, `models.py:25`): Multiple `hasattr(agent, "slug")` checks handle mixed types (old string agents vs. new Agent objects). **Action**: Verify if old string-based agent references still exist anywhere; if all agents are now objects, remove the fallback branches.

5. **Done! marker fallback** (`backend/src/services/copilot_polling/helpers.py:63-67`): Backward compatibility for issues created before the parent-issue-only policy change. **Action**: Assess if any pre-policy issues still exist in active projects; if not, remove the fallback.

6. **Frontend crypto polyfill** (`frontend/src/test/setup.ts:11`): Partial `crypto.randomUUID()` shim for test environments. **Action**: Keep — this is a legitimate test environment polyfill, not a backwards-compatibility shim.

**Alternatives considered**:
- **Remove all shims immediately**: Rejected — some may still have active callers. Each must be individually verified.
- **Leave all shims in place**: Rejected — this contradicts the cleanup goal. Verifiable dead shims should be removed.

### R2: Dead Code Detection Strategy

**Decision**: Use ruff (Python) and eslint/tsc (TypeScript) as the primary dead code detection tools, supplemented by manual grep-based cross-reference checking for patterns the tools cannot detect (e.g., unused route handlers, unused components that are still exported but never imported).

**Rationale**: Static analysis tools catch the low-hanging fruit (unused imports, variables, type definitions) automatically. Manual analysis is needed for higher-level patterns like unused routes or components that tools may not flag because they're still exported.

**Findings**:

1. **Backend**: Initial analysis shows no major dead functions or unused exceptions/constants — the codebase is relatively clean. All `utils.py` functions, `exceptions.py` classes, `constants.py` values, and `dependencies.py` functions are actively imported. **Action**: Run `ruff check --select F811,F841,F401` for comprehensive unused import/variable detection.

2. **Frontend**: `formatTime.ts` and `generateId.ts` utilities are actively used. No large commented-out code blocks found. **Action**: Run `eslint` and `tsc --noUnusedLocals --noUnusedParameters` for comprehensive detection.

3. **Commented-out code**: No significant commented-out code blocks found in either backend or frontend. The codebase is clean in this regard.

**Alternatives considered**:
- **vulture (Python dead code finder)**: Could supplement ruff but adds a new tool dependency; ruff covers the critical cases.
- **ts-prune (TypeScript unused exports)**: Could find unused exports but adds dependency; manual grep is sufficient for the scale of this codebase.

### R3: Duplication Consolidation Targets

**Decision**: Consolidation should focus on high-value targets where the duplication creates real maintenance risk. Low-value duplication (e.g., similar but not identical test setups) should be left if consolidation would create wrong abstractions.

**Rationale**: Constitution Principle V (Simplicity and DRY) states "Duplication is preferable to wrong abstraction." Each consolidation must be justified by genuine maintenance benefit.

**Findings**:

1. **Token client cache duplication** (`backend/src/services/completion_providers.py:67-80`, `backend/src/services/model_fetcher.py:75-80`): Both `CopilotCompletionProvider` and `GitHubCopilotModelFetcher` duplicate identical `_clients` dict, `_token_key()` hashing, and `_get_or_create_client()` caching. **Action**: Extract shared `TokenClientCache` utility class.

2. **Frontend CRUD hook patterns** (`frontend/src/hooks/useAgents.ts:15-63`, `frontend/src/hooks/useChores.ts:21-80+`): Nearly identical TanStack Query CRUD hooks (list, create, update, delete, chat). **Action**: Evaluate creating a `createResourceHooks<T>()` factory, but be cautious of premature abstraction — the two resources may diverge. Mark for consolidation only if the patterns remain stable.

3. **Frontend chat flow components** (`frontend/src/components/agents/AgentChatFlow.tsx`, `frontend/src/components/chores/ChoreChatFlow.tsx`): Near-duplicate chat message state, rendering, and session management with only naming differences. **Action**: Extract shared `GenericChatFlow` base component.

4. **Backend chat response models** (`backend/src/models/chat.py`, `backend/src/models/chores.py`, `backend/src/models/agents.py`): Three separate chat response models with similar structure (reply, session_id, is_complete). **Action**: Evaluate base `ChatFlowResponse` model, but only if the fields genuinely align — check for subtle differences first.

5. **Backend admin access check** (`backend/src/services/agent_creator.py`): `is_admin_user()` with duplicate database query. **Action**: Check if this is already in `settings_store.py` or similar; if not, consolidate.

6. **Backend test mock duplication**: Tests inconsistently use `factories.py`/`mocks.py` vs. inline mock setup. **Action**: Expand shared helpers and migrate the most duplicated patterns, but don't force every test to use shared helpers — some inline mocks are clearer in context.

**Alternatives considered**:
- **Aggressive consolidation of all similar patterns**: Rejected — risks creating wrong abstractions per Constitution Principle V.
- **No consolidation**: Rejected — the high-value targets (token cache, chat flow) have genuine maintenance risk from duplication.

### R4: Stale Test Identification Strategy

**Decision**: Identify stale tests by cross-referencing test targets with the current codebase. A test is stale if its target (function, class, route, component) no longer exists, or if it mocks so many internals that it doesn't test real behavior.

**Rationale**: Stale tests create false confidence and slow the test suite. However, removing a test that still validates real behavior would reduce coverage.

**Findings**:

1. **No test artifacts** (`.db` files, `MagicMock` files) found at the backend root level — the workspace is clean.
2. **No obviously stale test files** detected from the initial analysis — all test files appear to target existing code.
3. **Action**: The implementing agent should run the full test suites (`pytest`, `vitest`) first to identify any tests that fail or test nonexistent functionality, then do a targeted manual review.

**Alternatives considered**:
- **Delete all tests with heavy mocking**: Rejected — heavy mocking doesn't inherently mean the test is stale; it may test error paths or edge cases that are hard to test otherwise.
- **Coverage-based removal**: Rejected — low-coverage tests may still validate important edge cases.

### R5: Dependency and Hygiene Audit

**Decision**: Remove confirmed unused dependencies, stale environment variables, and stale TODO comments. Keep dependencies that are used indirectly or dynamically.

**Rationale**: Unused dependencies increase attack surface, slow installs, and confuse developers. Stale TODOs create noise.

**Findings**:

1. **Frontend unused dependency**: `socket.io-client@^4.7.4` is declared in `package.json` but no imports of `socket.io-client` were found in `frontend/src/`. **Action**: Verify it's not loaded dynamically, then remove.

2. **Frontend unused dev dependency**: `jsdom@^27.4.0` is listed but the project uses `happy-dom` (configured in test/setup.ts). **Action**: Verify it's not referenced in vitest config, then remove.

3. **~~Unused environment variable~~**: `SESSION_EXPIRE_HOURS` in `.env.example` was initially identified as unused, but further review confirmed it IS actively used: `backend/src/config.py:37` reads it as `session_expire_hours` (Pydantic auto-maps env vars), and `backend/src/services/session_store.py` references this config value. **Action**: Keep — not unused.

4. **TODO/FIXME comments**:
   - `backend/src/api/projects.py:23` — `# TODO: Also fetch org projects the user has access to` — May be future work, not completed work. **Action**: Keep unless confirmed as completed.
   - `backend/src/services/signal_chat.py:155,159,165` — `# TODO(bug-bash): Security — this leaks internal exception details` — Active security issue, not stale. **Action**: Keep (or fix the security issue, which is out of scope for cleanup).

5. **All backend Python dependencies** in `pyproject.toml` are actively imported.
6. **All Docker Compose services** are active and referenced.
7. **All migration files** (001-010) are active and properly sequenced.

**Alternatives considered**:
- **Remove all TODOs**: Rejected — some TODOs reference future work or active issues that should be preserved.
- **Keep all dependencies**: Rejected — unused dependencies should be removed for hygiene.

## Summary

All research tasks resolved. No NEEDS CLARIFICATION items remain. Key findings:

1. **Backwards-compatibility shims**: 5 candidates identified for removal after individual verification (plaintext token fallback, model re-exports, service re-exports, hasattr fallbacks, Done! marker fallback). 1 polyfill should be kept (crypto in tests).
2. **Dead code**: The codebase is relatively clean — no major dead functions or commented-out code blocks found. Static analysis tools should be run for comprehensive coverage.
3. **Duplication**: 6 consolidation targets identified — highest value are token client cache (backend), chat flow components (frontend), and CRUD hooks (frontend).
4. **Stale tests**: No obviously stale tests detected. Full test suite run needed for definitive assessment.
5. **Hygiene**: 2 unused npm dependencies (`socket.io-client`, `jsdom`), 2 TODO clusters (1 future work, 1 active security issue — both should be kept). Note: `SESSION_EXPIRE_HOURS` was initially identified as unused but is actually active (see R5 finding #3).
