# Contract: Label Utilities

**Branch**: `034-label-pipeline-state` | **Phase**: 1

## Purpose

Provide pure-function utilities for constructing, parsing, and querying pipeline state labels. These functions are the foundation used by all other phases — write path, fast-path read, and validation.

## Interface

**Location**: `backend/src/constants.py`

```python
# Constants
PIPELINE_LABEL_PREFIX: str = "pipeline:"
AGENT_LABEL_PREFIX: str = "agent:"
ACTIVE_LABEL: str = "active"
STALLED_LABEL: str = "stalled"
PIPELINE_LABEL_COLOR: str = "0052cc"
AGENT_LABEL_COLOR: str = "7057ff"
ACTIVE_LABEL_COLOR: str = "0e8a16"
STALLED_LABEL_COLOR: str = "d73a4a"

# Parsing: label string → extracted value
def extract_pipeline_config(label_name: str) -> str | None: ...
def extract_agent_slug(label_name: str) -> str | None: ...

# Building: value → label string
def build_pipeline_label(config_name: str) -> str: ...
def build_agent_label(agent_slug: str) -> str: ...

# Querying: label list → extracted value
def find_pipeline_label(labels: list[dict[str, str]] | list) -> str | None: ...
def find_agent_label(labels: list[dict[str, str]] | list) -> str | None: ...
def has_stalled_label(labels: list[dict[str, str]] | list) -> bool: ...
```

## Invariants

- All parsing functions are **pure** — no I/O, no side effects, no exceptions.
- `extract_*` functions return `None` for non-matching labels, never raise.
- `build_*` functions produce labels that round-trip through `extract_*`:
  - `extract_pipeline_config(build_pipeline_label("x"))` == `"x"`
  - `extract_agent_slug(build_agent_label("x"))` == `"x"`
- `find_*` functions accept both `list[dict]` and `list[Label]` (duck-typed via `.get()` / `getattr()`).
- Label names must comply with GitHub constraints: max 50 characters, no commas.
- Empty or whitespace-only config names / agent slugs are **not validated** at the utility level — callers are responsible for input validation.
