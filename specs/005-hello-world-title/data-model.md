# Data Model: Update App Title to "Hello World"

**Feature**: 005-hello-world-title  
**Date**: 2026-02-19  
**Status**: Complete

## Overview

This feature involves no new data entities, database changes, or state transitions. It is a static text replacement across existing files. The "data model" for this feature is the inventory of title reference locations and their replacement values.

## Title Reference Model

### Entity: Title Reference

| Field | Type | Description |
|-------|------|-------------|
| file_path | string | Absolute path to the file containing the reference |
| current_value | string | Current text containing "Agent Projects" |
| new_value | string | Replacement text containing "Hello World" |
| category | enum | `display`, `metadata`, `test`, `config`, `documentation` |
| priority | enum | `P1` (user-facing), `P2` (metadata), `P3` (tests/config) |

### Reference Inventory

| # | File | Category | Current → New |
|---|------|----------|---------------|
| 1 | `frontend/index.html` | display | `<title>Agent Projects</title>` → `<title>Hello World</title>` |
| 2 | `frontend/src/App.tsx` (line 72) | display | `<h1>Agent Projects</h1>` → `<h1>Hello World</h1>` |
| 3 | `frontend/src/App.tsx` (line 89) | display | `<h1>Agent Projects</h1>` → `<h1>Hello World</h1>` |
| 4 | `backend/src/main.py` | metadata | `title="Agent Projects API"` → `title="Hello World API"` |
| 5 | `backend/src/main.py` | metadata | `description="REST API for Agent Projects"` → `description="REST API for Hello World"` |
| 6 | `backend/src/main.py` | metadata | `"Starting Agent Projects API"` → `"Starting Hello World API"` |
| 7 | `backend/src/main.py` | metadata | `"Shutting down Agent Projects API"` → `"Shutting down Hello World API"` |
| 8 | `backend/pyproject.toml` | metadata | `"FastAPI backend for Agent Projects"` → `"FastAPI backend for Hello World"` |
| 9 | `backend/README.md` | documentation | `Agent Projects` → `Hello World` (headings and descriptions) |
| 10 | `.devcontainer/devcontainer.json` | config | `"name": "Agent Projects"` → `"name": "Hello World"` |
| 11 | `.env.example` | config | `# Agent Projects` → `# Hello World` |
| 12 | `frontend/src/types/index.ts` | documentation | JSDoc `Agent Projects` → `Hello World` |
| 13 | `frontend/src/services/api.ts` | documentation | JSDoc `Agent Projects` → `Hello World` |
| 14-21 | `frontend/e2e/*.spec.ts` | test | All `'Agent Projects'` → `'Hello World'` in assertions |

### Validation Rules

- No instance of "Agent Projects" should remain in any file after the update (FR-005)
- The exact string "Hello World" must be used (no variations like "HelloWorld" or "Hello, World")
- HTML entity encoding is not needed (plain ASCII text)

### State Transitions

N/A — This feature has no state machine. It is a one-time, idempotent text replacement.

## Relationships

No entity relationships. All references are independent string literals with no shared state or configuration dependency.
