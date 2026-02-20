# Data Model: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20 | **Phase**: 1

## Overview

This feature does not introduce new data entities or modify existing data models. The work is purely additive — writing tests and fixing bugs — so the existing data model remains unchanged. This document catalogs the existing entities that tests will validate.

## Existing Entities (Test Targets)

### Backend Models (Pydantic)

| Entity | File | Key Fields | Validation Rules |
|--------|------|------------|-----------------|
| User | `backend/src/models/user.py` | id, username, access_token | GitHub OAuth fields |
| Project | `backend/src/models/project.py` | id, name, owner, columns | GitHub project board representation |
| Board | `backend/src/models/board.py` | columns, issues, agents | Kanban board state |
| Task | `backend/src/models/task.py` | id, title, status, assignee | Issue/task card |
| Chat | `backend/src/models/chat.py` | messages, context | Chat session state |
| Settings | `backend/src/models/settings.py` | ai_preferences, display, notifications | User configuration |

### Frontend Types (TypeScript)

| Entity | File | Description |
|--------|------|-------------|
| Types index | `frontend/src/types/index.ts` | Shared TypeScript interfaces for all entities |

### State Transitions

No new state transitions are introduced. Existing state transitions to be validated by tests:

1. **Issue lifecycle**: `open` → `in_progress` → `done` (board columns)
2. **Auth flow**: `unauthenticated` → `authenticating` → `authenticated` / `error`
3. **WebSocket connection**: `disconnected` → `connecting` → `connected` / `reconnecting`

## Relationships

```text
User ──1:N──▶ Project
Project ──1:N──▶ Board Column
Board Column ──1:N──▶ Issue/Task
User ──1:1──▶ Settings
User ──1:N──▶ Chat Session
Chat Session ──1:N──▶ Message
```

## No Schema Changes

This feature introduces zero schema changes. All test data will be constructed via:
- **Backend**: pytest fixtures in `conftest.py` and inline test data
- **Frontend**: mock objects and test utilities in `src/test/`
