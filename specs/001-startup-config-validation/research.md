# Research: Startup Config Validation

**Feature**: 001-startup-config-validation
**Date**: 2026-03-22
**Status**: Complete — all unknowns resolved

## Research Tasks

### R-001: Existing validation pattern in `_validate_production_secrets()`

**Question**: How does the current validator accumulate and raise errors?

**Finding**: The validator at `solune/backend/src/config.py:104-164` uses a `@model_validator(mode="after")` decorator. It:
1. Creates a local `errors: list[str] = []`
2. Branches on `self.debug` (production vs debug mode)
3. In production (`not self.debug`): appends descriptive messages to `errors`, then raises `ValueError("Production configuration errors:\n  - " + "\n  - ".join(errors))` if any accumulated
4. In debug mode (`else`): emits `_logger.warning()` for each missing/weak value

**Decision**: Follow the identical pattern — append to `errors` in the production block, emit `_logger.warning()` in the debug block. The `ai_provider` enum check is a special case: it raises `ValueError` before the `if not self.debug` branch, making it fatal in both modes.

**Rationale**: Consistency with existing code reduces cognitive overhead and review friction.

**Alternatives considered**: None — the existing pattern is well-established and appropriate.

---

### R-002: Validation insertion point and ordering

**Question**: Where exactly in `_validate_production_secrets()` should the new validations go?

**Finding**: The spec mandates this order:
1. **AI provider enum check** (universal — before the `if not self.debug` split, line ~113)
2. **Azure OpenAI completeness** (branched — production error / debug warning, inside respective blocks)
3. **Database path** (production block only, after existing checks)

**Decision**: Insert the ai_provider check immediately after `errors: list[str] = []` (line 112) and before `if not self.debug:` (line 114). Add Azure OpenAI check and DB path check within the existing production/debug branches.

**Rationale**: Placing the universal check first ensures it runs regardless of mode. Following the spec's prescribed order keeps the implementation traceable to requirements.

**Alternatives considered**: Adding a separate `@model_validator` — rejected because the spec explicitly states "no new validators or methods needed" and adding one would violate Simplicity (Constitution V).

---

### R-003: `Path.is_absolute()` behavior for `:memory:` and edge cases

**Question**: How does `pathlib.Path(":memory:").is_absolute()` behave? What about empty strings and whitespace?

**Finding**:
- `Path(":memory:").is_absolute()` → `False` (it's a relative path)
- `Path("").is_absolute()` → `False`
- `Path("  ").is_absolute()` → `False`
- The spec says: check `database_path` is empty OR (not `:memory:` AND not absolute)

**Decision**: Validation logic:
```python
db = self.database_path.strip()
if not db:
    errors.append("DATABASE_PATH must not be empty ...")
elif db != ":memory:" and not Path(db).is_absolute():
    errors.append("DATABASE_PATH must be an absolute path ...")
```

**Rationale**: Strip first to catch whitespace-only values (edge case from spec). Check `:memory:` as a special bypass before absoluteness. No directory existence checks per FR-008.

**Alternatives considered**: Using `os.path.isabs()` — rejected because `pathlib.Path.is_absolute()` is the spec's explicit requirement and is the more modern API.

---

### R-004: Existing test helpers compatibility

**Question**: Do `_make_production()` and `_make_debug()` need changes for the new validations?

**Finding**: Examined `test_config_validation.py:17-44`:
- `_make_production()` defaults: `ai_provider` not explicitly set → falls back to `Settings` default `"copilot"`, `database_path` not set → falls back to `"/var/lib/solune/data/settings.db"` (absolute path)
- `_make_debug()` defaults: same fallbacks apply

**Decision**: No changes needed to helpers. The existing defaults (`ai_provider="copilot"`, `database_path="/var/lib/solune/data/settings.db"`) pass all new validations. Tests needing invalid values use the `**overrides` mechanism.

**Rationale**: Preserves backward compatibility of all existing tests — no risk of regression.

**Alternatives considered**: None needed.

---

### R-005: Azure OpenAI credential field semantics

**Question**: How are `azure_openai_endpoint` and `azure_openai_key` represented when "missing"?

**Finding**: Both are `str | None` with defaults of `None` in `config.py:33-34`. A "missing" credential is `None`. An "empty" credential is `""`. The spec says to check "missing or empty" — validation should treat both `None` and `""` as missing.

**Decision**: Use `not self.azure_openai_endpoint` and `not self.azure_openai_key` — this catches both `None` and `""` (and whitespace-only, though that's unlikely from env vars).

**Rationale**: Consistent with existing checks in the validator (e.g., `if not self.encryption_key`).

**Alternatives considered**: Explicit `is None or == ""` — rejected as unnecessarily verbose when truthy check suffices.

---

### R-006: Error message format

**Question**: What format should error messages follow?

**Finding**: Spec FR-009 requires every error message to include: (1) what is wrong, and (2) how to fix it. Existing examples follow this pattern:
- `"ENCRYPTION_KEY is required in production mode. Generate one with: ..."`
- `"SESSION_SECRET_KEY must be at least 64 characters (current length: N). Generate one with: ..."`

**Decision**: Follow the same two-part format:
- AI provider: `"Unknown AI_PROVIDER '{value}'. Accepted values are: 'copilot', 'azure_openai'."`
- Azure endpoint: `"AZURE_OPENAI_ENDPOINT is required when AI_PROVIDER='azure_openai'. Set it to your Azure OpenAI resource URL."`
- Azure key: `"AZURE_OPENAI_KEY is required when AI_PROVIDER='azure_openai'. Set it to your Azure OpenAI API key."`
- DB empty: `"DATABASE_PATH must not be empty in production mode. Set it to an absolute path (e.g., /var/lib/solune/data/settings.db)."`
- DB relative: `"DATABASE_PATH must be an absolute path in production mode (got '{value}'). Use a full path starting with /."`

**Rationale**: Consistent tone and structure with existing error messages.

**Alternatives considered**: None.

## Summary

All technical unknowns have been resolved. No NEEDS CLARIFICATION items remain. The implementation is straightforward: ~25 lines of validation logic in a single existing method, ~60 lines of tests across 3 new test classes using existing helpers.
