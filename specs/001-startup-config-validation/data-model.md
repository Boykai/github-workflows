# Data Model: Startup Config Validation

**Feature**: 001-startup-config-validation
**Date**: 2026-03-22

## Entities

### Settings (existing — modified)

The `Settings` class (`solune/backend/src/config.py`) is the single entity affected by this feature. No new entities are introduced.

| Field | Type | Default | Validation Added |
|-------|------|---------|-----------------|
| `ai_provider` | `str` | `"copilot"` | Must be in `{"copilot", "azure_openai"}` — fatal in all modes |
| `azure_openai_endpoint` | `str \| None` | `None` | Required when `ai_provider == "azure_openai"` (prod error / debug warning) |
| `azure_openai_key` | `str \| None` | `None` | Required when `ai_provider == "azure_openai"` (prod error / debug warning) |
| `database_path` | `str` | `"/var/lib/solune/data/settings.db"` | Must be non-empty and absolute in production (`:memory:` exempt) |

### Validation Rules

```
ai_provider ∈ {"copilot", "azure_openai"}                     → ValueError (universal)

ai_provider == "azure_openai" ∧ ¬azure_openai_endpoint        → error (prod) / warning (debug)
ai_provider == "azure_openai" ∧ ¬azure_openai_key             → error (prod) / warning (debug)

database_path.strip() == ""                                    → error (prod only)
database_path ≠ ":memory:" ∧ ¬Path(database_path).is_absolute → error (prod only)
```

### Relationships

- `ai_provider` determines whether `azure_openai_endpoint` and `azure_openai_key` are required (conditional dependency).
- `database_path` is independent of `ai_provider`.
- All validations occur inside the existing `_validate_production_secrets()` model validator — no new relationships introduced.

### State Transitions

Not applicable. Configuration validation is a one-shot operation at boot time. There are no state transitions — the application either starts successfully or raises `ValueError` and exits.
