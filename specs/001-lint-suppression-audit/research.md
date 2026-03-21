# Research: Lint & Type Suppression Audit

**Feature**: 001-lint-suppression-audit | **Date**: 2026-03-21

## Baseline Suppression Inventory

| Category | Location | Count | Directive |
|----------|----------|-------|-----------|
| Backend type suppressions | `solune/backend/src/` | 39 | `# type: ignore[...]` |
| Backend pyright directives | `solune/backend/src/` | 10 | `# pyright: ...` |
| Backend noqa suppressions | `solune/backend/src/` | 21 | `# noqa: ...` |
| Frontend eslint suppressions | `solune/frontend/src/` | 14 | `eslint-disable-next-line` |
| Backend test type suppressions | `solune/backend/tests/` | 26 | `# type: ignore[...]` |
| Frontend test ts-expect-error | `solune/frontend/src/` | 5 | `@ts-expect-error` |
| **Total** | | **115** | |

**Target**: Reduce by ≥50% → ≤58 remaining.

---

## Category 1: Backend `# type: ignore[return-value]` (12 instances)

### Decision: Use `cast(T, value)` in `cached_fetch()` and individual call sites

### Rationale

The root cause is `InMemoryCache.get()` returning `Any | None`. The `cached_fetch[T]()` function signature promises `T` but the cache only proves `Any`. Using `typing.cast(T, cached)` is the minimal correct fix — it communicates intent ("I know this is T because I stored it as T") without restructuring the cache internals.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Make `InMemoryCache` generic with `CacheEntry[T]` | Over-engineering: cache stores heterogeneous types; making it generic would require multiple typed caches or `Any` anyway |
| Add runtime `isinstance` checks | Impossible: `T` is erased at runtime; cannot check `isinstance(cached, T)` |
| Suppress globally in pyright config | Violates FR-003: must fix underlying issue, not weaken rules |

### Resolution Strategy

**Files affected** (12 instances):
- `src/services/cache.py` (lines 220, 229, 234) — add `from typing import cast`; replace `return cached  # type: ignore[return-value]` with `return cast(T, cached)`
- `src/services/github_projects/copilot.py` (lines 233, 816) — same pattern
- `src/services/github_projects/pull_requests.py` (lines 289, 369, 712) — same pattern
- `src/services/github_projects/projects.py` (line 357) — same pattern
- `src/services/github_projects/issues.py` (line 435) — same pattern
- `src/utils.py` (line 297) — same pattern

**Estimated removals**: 12

---

## Category 2: Backend `# type: ignore[type-arg]` — asyncio.Task (6 instances)

### Decision: Add explicit type parameter `asyncio.Task[None]` or `asyncio.Task[Any]`

### Rationale

Pyright (Python 3.13 target) requires `asyncio.Task` to have a type argument. All tasks in `task_registry.py` are fire-and-forget (no return value consumed), so `asyncio.Task[None]` is correct. For eviction callbacks in `service.py` and `model_fetcher.py`, tasks may wrap arbitrary coroutines, so `asyncio.Task[Any]` is appropriate.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Use `asyncio.Task[object]` | Too restrictive; doesn't convey "any return type" semantics |
| Suppress globally | Violates FR-003 |

### Resolution Strategy

**Files affected** (6 instances):
- `src/services/task_registry.py` (lines 33, 44, 55, 101) — change `asyncio.Task` to `asyncio.Task[None]`
- `src/services/github_projects/service.py` (line 89) — change to `asyncio.Task[Any]`
- `src/services/model_fetcher.py` (line 28) — change to `asyncio.Task[Any]`

**Estimated removals**: 6

---

## Category 3: Backend `# type: ignore[reportMissingImports]` (5 instances)

### Decision: Retain suppressions with improved justification comments

### Rationale

These imports are from optional packages (`copilot` SDK, `openai`) that may not be installed in all environments. The imports occur inside runtime functions (not at module level), so `TYPE_CHECKING` guards would not help — the actual import must happen at runtime. The `# type: ignore[reportMissingImports]` is the correct mechanism for optional runtime imports. However, each must have a clear justification comment.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Move to `TYPE_CHECKING` guard + runtime import | Already uses runtime import pattern; TYPE_CHECKING would only help for type annotations, not runtime instantiation |
| Create local type stubs | Out of scope per spec (Scope Boundaries) |
| Install packages as required deps | They are intentionally optional (not all deployments use Copilot SDK or Azure OpenAI) |

### Resolution Strategy

**Files affected** (5 instances in `src/services/completion_providers.py`):
- Lines 62–63: `from copilot import CopilotClient, SubprocessConfig` — retain with justification: "optional copilot SDK; not installed in all environments"
- Line 167–168: `from copilot import PermissionHandler, SessionEventType` — same justification
- Line 262: `from openai import AzureOpenAI` — retain with justification: "optional openai SDK; only used when Azure OpenAI is configured"

**Estimated removals**: 0 (all justified and retained with comments)

---

## Category 4: Backend `# type: ignore[arg-type]` (7 instances)

### Decision: Fix with proper type annotations, casts, or narrowing

### Rationale

Each `arg-type` suppression has a specific underlying cause that can be resolved:

### Resolution Strategy

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `completion_providers.py:280` | `endpoint=settings.azure_openai_endpoint` | `str \| None` passed where `str` expected | Add `assert` or `if` guard before usage |
| `completion_providers.py:281` | `credential=AzureKeyCredential(...)` | Same `str \| None` issue | Same guard |
| `task_registry.py:50` | `asyncio.create_task(coro, name=name)` | `name` parameter type mismatch | Fix parameter type annotation |
| `agents/service.py:1143` | `_chat_session_timestamps.get` | `dict.get` returns `V \| None`, `min()` needs `V` | Use `key=lambda k: _chat_session_timestamps[k]` |
| `utils.py:141` | `self._data.pop(key, *args)` | Variadic args type mismatch | Use explicit default parameter |
| `main.py:482` | `_rate_limit_exceeded_handler` | Handler signature mismatch | Add proper callable type annotation |
| `tools/service.py:710` | `dict(next(iter(...)))` | `arg-type` on dict constructor | Use explicit type annotation or cast |

**Estimated removals**: 7

---

## Category 5: Backend `# pyright: reportAttributeAccessIssue=false` (8 file-level + 2 inline)

### Decision: Retain file-level directives with justification comments; fix 2 inline instances

### Rationale

The 8 file-level `# pyright: reportAttributeAccessIssue=false` directives in `github_projects/*.py` exist because these modules access attributes on GitHub API response objects (from `httpx` or `gql`) that are dynamically typed. The response objects use dynamic attribute access patterns that Pyright cannot statically verify. Removing these file-level directives would require typing every GitHub API response with TypedDict or dataclass, which is out of scope.

The 2 inline instances in `completion_providers.py` (lines 66 and 184) are for the optional `copilot` SDK whose type stubs may not be available.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Create TypedDict for all GitHub API responses | Massive scope creep; hundreds of response shapes |
| Use `Any` type annotations on all response vars | Would introduce new `no-explicit-any` warnings |
| Narrow to specific lines instead of file-level | Too many attribute accesses per file; file-level is cleaner |

### Resolution Strategy

- 8 file-level directives: **Retain** with justification comment: "GitHub API responses use dynamic attribute access; typing all response shapes is out of scope"
- 2 inline `pyright: ignore[...]`: **Retain** with justification: "optional copilot SDK; type stubs may not be available"

**Estimated removals**: 0 (all justified)

---

## Category 6: Backend `# noqa: B008` — FastAPI Depends() (12 instances)

### Decision: Add `B008` to global `ignore` list in `pyproject.toml`; remove all inline suppressions

### Rationale

FastAPI's `Depends()` in function parameter defaults is a well-known false positive for B008 ("Do not perform function calls in argument defaults"). The FastAPI documentation explicitly recommends this pattern. A global ignore is the cleanest solution per FR-009.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Per-file ignores in `[tool.ruff.lint.per-file-ignores]` for `src/api/*.py` | Would still need to include `src/dependencies.py`; global ignore is simpler |
| Keep inline `# noqa: B008` on each line | Violates FR-009; adds noise to every route definition |

### Resolution Strategy

1. Add `"B008"` to `[tool.ruff.lint] ignore` list in `pyproject.toml` with comment: `# function call defaults (FastAPI Depends() pattern)`
2. Remove all 12 `# noqa: B008` comments from `src/api/cleanup.py`, `src/api/activity.py`, `src/api/chat.py`, `src/dependencies.py`

**Estimated removals**: 12

---

## Category 7: Backend `# noqa: F401` — Re-exports (6 instances)

### Decision: Add `__all__` declarations; remove inline suppressions

### Rationale

The `# noqa: F401` directives exist on imports that are re-exported for backward compatibility. Adding an explicit `__all__` list makes the public API explicit and tells Ruff that these imports are intentionally re-exported. Both affected files (`src/models/chat.py` and `src/services/copilot_polling/__init__.py`) need `__all__` lists.

**Note**: `src/services/copilot_polling/__init__.py` already has an `__all__` list (lines 150–242), so removing the `# noqa: F401` should work immediately once verified. `src/models/chat.py` needs an `__all__` to be added.

### Resolution Strategy

1. `src/models/chat.py`: Add `__all__` listing all re-exported names; remove `# noqa: F401` from import lines
2. `src/services/copilot_polling/__init__.py`: Remove `# noqa: F401` (already has `__all__`)

**Estimated removals**: 6

---

## Category 8: Backend `# noqa: E402` (1 instance) and `# noqa: PTH118/PTH119` (2 instances)

### Decision: Retain all 3 with justification comments

### Rationale

- **E402** (`github_projects/__init__.py` line 60): Import after module-level code — necessary because the import depends on prior setup. Justified.
- **PTH119** (`api/chat.py` line 381): `os.path.basename()` — CodeQL recognizes this as a path-traversal sanitizer. Switching to `Path.name` may break CodeQL's security analysis. **Security-critical; must retain.**
- **PTH118** (`api/chat.py` line 387): `os.path.normpath(os.path.join(...))` — Same CodeQL sanitizer chain. **Security-critical; must retain.**

### Resolution Strategy

- Add/improve justification comments on all 3 lines
- No code changes needed

**Estimated removals**: 0 (all justified — 2 are security-critical)

---

## Category 9: Backend Other `# type: ignore` (7 miscellaneous instances)

### Decision: Fix individually

### Resolution Strategy

| File | Line | Rule | Fix |
|------|------|------|-----|
| `config.py:217` | `call-arg` | `Settings()` no-arg | Add justification: "pydantic-settings loads from env" (already has comment) |
| `logging_utils.py:198,200` | `attr-defined` | `record.request_id` | Retain: dynamic attribute injection on `LogRecord` is standard Python logging pattern |
| `logging_utils.py:301` | `return-value` | Decorator wrapper return | Fix with `cast()` or `@overload` |
| `metadata_service.py:371-373` | `index` | `row[0]`, `row[1]`, `row[2]` | Fix with proper tuple unpacking or type annotation |
| `workflow_orchestrator/config.py:283` | `assignment` | `config.agent_mappings = deduped` | Fix with proper type annotation on `deduped` |
| `api/workflow.py:578` | `assignment` | Same pattern | Same fix |
| `utils.py:140` | `misc` | `BoundedDict.pop` override | Retain with justification (intentional API widening) |

**Estimated removals**: 4 (fix 4, retain 3)

---

## Category 10: Frontend `eslint-disable` — jsx-a11y (5 instances)

### Decision: Retain 2 autofocus, fix 3 backdrop-dismiss patterns

### Rationale

**Autofocus** (`AddAgentPopover.tsx:114`, `AddChoreModal.tsx:276`): `autoFocus` on search/name inputs in popover/modal context is an intentional UX decision. Focus management on modal open is standard practice. Retain with justification.

**Backdrop dismiss** (`AgentIconPickerModal.tsx:59`, `AgentPresetSelector.tsx:424,472`): These use `<div role="dialog" onClick={stopPropagation}>` which triggers `click-events-have-key-events` and `no-noninteractive-element-interactions`. The parent backdrop `<div>` already has `onKeyDown` for Escape. The inner dialog div's `stopPropagation` click handler is needed to prevent backdrop close. These have proper `role="dialog"` and `aria-modal="true"`. Can be resolved by either: (a) adding `onKeyDown` to inner div, or (b) using `<dialog>` element.

### Resolution Strategy

- `AddAgentPopover.tsx:114`: Retain suppression with justification comment
- `AddChoreModal.tsx:276`: Retain suppression with justification comment
- `AgentIconPickerModal.tsx:59`: Replace `<div>` with semantic element or add keyboard handler to remove suppression
- `AgentPresetSelector.tsx:424,472`: Same approach for both confirmation dialogs

**Estimated removals**: 3 (fix backdrop patterns), retain 2 (autofocus)

---

## Category 11: Frontend `eslint-disable` — react-hooks/exhaustive-deps (7 instances)

### Decision: Fix 4, retain 3 with justification

### Rationale

| File | Decision | Reason |
|------|----------|--------|
| `ChatInterface.tsx:389` | **FIX** | Remove conditional; simplify to unconditional `setMentionValidationError(null)` on token change. Add `mentionValidationError` or remove the condition |
| `AgentChatFlow.tsx:65` | **RETAIN** | Initialization-only effect (empty deps `[]`); standard React pattern for fire-once effects. Add justification comment |
| `ModelSelector.tsx:86` | **FIX** | Missing `isOpen` dependency can be added safely |
| `UploadMcpModal.tsx:201` | **FIX** | Missing `name` dependency — effect uses `name` but doesn't list it |
| `AddChoreModal.tsx:90` | **FIX** | Missing `resetAndClose` dependency — potential stale closure bug |
| `ChoreChatFlow.tsx:62` | **RETAIN** | Same initialization-only pattern as AgentChatFlow. Add justification comment |
| `useRealTimeSync.ts:219` | **RETAIN** | Already has justification comment explaining `connect` stability. Acceptable |

**Estimated removals**: 4 (fix deps), retain 3 (justified initialization patterns)

---

## Category 12: Frontend `eslint-disable` — @typescript-eslint/no-explicit-any (2 instances)

### Decision: Fix 1, retain 1

### Rationale

- `useVoiceInput.ts:42`: `window as any` for `webkitSpeechRecognition` — **FIX** by creating a typed `WindowWithSpeechRecognition` interface
- `lazyWithRetry.ts:13`: `ComponentType<any>` — **RETAIN** with justification. `any` is required here because React's `ComponentType` generic must accept arbitrary props shapes. There is no `unknown`-compatible alternative that works with `React.lazy()`

**Estimated removals**: 1

---

## Category 13: Backend Test `# type: ignore` (26 instances)

### Decision: Fix 17, retain 9

### Rationale

| File | Count | Decision | Reason |
|------|-------|----------|--------|
| `test_logging_utils.py` | 5 | **RETAIN** | Dynamic `record.request_id` attribute on `LogRecord` — standard Python logging pattern; no typed alternative |
| `test_metadata_service.py` | 8 | **FIX** | Access to `_l1.data`, `_l1.set_calls`, `_l1.deleted` on spy cache — add explicit type annotations to spy class |
| `test_polling_loop.py` | 1 | **RETAIN** | Frozen dataclass mutation test — suppression is intentional |
| `test_transcript_detector.py` | 1 | **RETAIN** | Same frozen dataclass pattern |
| `test_template_files.py` | 1 | **FIX** | Fix generator return type annotation |
| `test_pipeline_state_store.py` | 1 | **FIX** | Use `{**defaults, **overrides}` dict merge instead of `.update()` |
| `test_agent_output.py` | 1 | **RETAIN** | Frozen dataclass mutation test |
| `test_transaction_safety.py` | 2 | **FIX** | Use `unittest.mock.patch.object()` or `MagicMock()` |
| `test_production_mode.py` | 6 | **FIX** | Already has inline comment "pydantic-settings loads from env"; the `call-arg` can be resolved with explicit `_env_file=None` parameter or cast |

**Estimated removals**: 17

---

## Category 14: Frontend `@ts-expect-error` in Tests (5 instances)

### Decision: Retain all 5 with justification comments

### Rationale

All 5 instances override `global.WebSocket` or `globalThis.crypto` for test setup — assigning to read-only DOM globals. TypeScript correctly flags this as an error. The `@ts-expect-error` is the correct mechanism for intentional test-only global overrides. No typed alternative exists without introducing a full DOM mock abstraction (out of scope).

**Estimated removals**: 0

---

## Projected Outcome

| Category | Baseline | Removals | Retained | Notes |
|----------|----------|----------|----------|-------|
| Backend `type: ignore` (src) | 39 | 29 | 10 | cast(), type params, narrowing |
| Backend `pyright:` (src) | 10 | 0 | 10 | GitHub API dynamic access justified |
| Backend `noqa` (src) | 21 | 18 | 3 | B008 global, F401 __all__, retain E402+PTH |
| Frontend `eslint-disable` | 14 | 8 | 6 | a11y fixes, deps fixes, retain justified |
| Backend test `type: ignore` | 26 | 17 | 9 | spy typing, mock patterns |
| Frontend `@ts-expect-error` | 5 | 0 | 5 | Test global overrides justified |
| **Total** | **115** | **72** | **43** | **63% reduction** ✅ |

**Success criteria SC-001** (≥50% reduction): ✅ Met — 63% reduction (72 removed, 43 retained)
**Success criteria SC-002** (100% retained have justification): Will be enforced during implementation
