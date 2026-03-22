# Quickstart: Startup Config Validation

**Feature**: 001-startup-config-validation
**Date**: 2026-03-22

## Overview

This feature adds three startup-time validations to the existing `Settings` class in `config.py`:

1. **AI Provider enum check** — rejects unknown `AI_PROVIDER` values (fatal in all modes)
2. **Azure OpenAI completeness** — requires endpoint + key when provider is `azure_openai`
3. **Database path validation** — enforces non-empty, absolute paths in production

## Files Modified

| File | Change Type | Lines Added |
|------|------------|-------------|
| `solune/backend/src/config.py` | Modified | ~25 |
| `solune/backend/tests/unit/test_config_validation.py` | Modified | ~60 |

## Implementation Steps

### Step 1: Add ai_provider enum validation (config.py)

Insert **before** the `if not self.debug:` branch in `_validate_production_secrets()`:

```python
_VALID_AI_PROVIDERS = {"copilot", "azure_openai"}
if self.ai_provider not in _VALID_AI_PROVIDERS:
    raise ValueError(
        f"Unknown AI_PROVIDER '{self.ai_provider}'. "
        f"Accepted values are: {', '.join(sorted(_VALID_AI_PROVIDERS))}."
    )
```

### Step 2: Add Azure OpenAI completeness check (config.py)

In the **production block** (`if not self.debug:`), append:

```python
if self.ai_provider == "azure_openai":
    if not self.azure_openai_endpoint:
        errors.append(
            "AZURE_OPENAI_ENDPOINT is required when AI_PROVIDER='azure_openai'. "
            "Set it to your Azure OpenAI resource URL."
        )
    if not self.azure_openai_key:
        errors.append(
            "AZURE_OPENAI_KEY is required when AI_PROVIDER='azure_openai'. "
            "Set it to your Azure OpenAI API key."
        )
```

In the **debug block** (`else:`), append:

```python
if self.ai_provider == "azure_openai" and (
    not self.azure_openai_endpoint or not self.azure_openai_key
):
    _logger.warning(
        "Azure OpenAI credentials incomplete — AI features will not work (debug mode)"
    )
```

### Step 3: Add database path validation (config.py)

In the **production block** only, after Azure OpenAI check:

```python
_db = self.database_path.strip()
if not _db:
    errors.append(
        "DATABASE_PATH must not be empty in production mode. "
        "Set it to an absolute path (e.g., /var/lib/solune/data/settings.db)."
    )
elif _db != ":memory:" and not Path(_db).is_absolute():
    errors.append(
        f"DATABASE_PATH must be an absolute path in production mode "
        f"(got '{self.database_path}'). Use a full path starting with /."
    )
```

Add `from pathlib import Path` at the top of `config.py`.

### Step 4: Add test classes (test_config_validation.py)

Add three new test classes using existing `_make_production()` / `_make_debug()` helpers:

- `TestAiProviderValidation` — 3 tests (unknown raises, copilot passes, azure_openai passes)
- `TestAzureOpenAIConfigRequired` — 4 tests (missing endpoint, missing key, complete passes, debug warns)
- `TestDatabasePathValidation` — 4 tests (empty raises, relative raises, absolute passes, debug allows relative)

## Verification

```bash
# Run new + existing validation tests
pytest tests/unit/test_config_validation.py -v

# Verify no regression on config property tests
pytest tests/unit/test_config.py -v
```

## Configuration Reference

| Environment Variable | Required When | Valid Values |
|---------------------|---------------|--------------|
| `AI_PROVIDER` | Always | `copilot`, `azure_openai` |
| `AZURE_OPENAI_ENDPOINT` | `AI_PROVIDER=azure_openai` (prod) | URL string |
| `AZURE_OPENAI_KEY` | `AI_PROVIDER=azure_openai` (prod) | API key string |
| `DATABASE_PATH` | Production mode | Absolute path or `:memory:` |
