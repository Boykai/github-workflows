# Implementation Plan: GitHub Projects Chat Interface

**Branch**: `001-github-project-chat` | **Date**: 2026-01-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-github-project-chat/spec.md`

## Summary

A web-based chat interface enabling developers to manage GitHub Projects V2 through natural language interactions. Users authenticate via GitHub OAuth, select from their organization/user/repository projects, and create tasks or update statuses using AI-powered chat commands. The system uses Azure OpenAI for natural language understanding and plans for future Microsoft Agent Framework integration.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**:
- Backend: FastAPI, httpx, python-jose (JWT), pydantic, azure-ai-inference
- Frontend: React 18+, Vite, TanStack Query, Socket.io-client
**Storage**: In-memory session storage (MVP), Redis for token caching (future)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux server (Docker), Modern web browsers
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Task creation <10 seconds, concurrent users 100+
**Constraints**: GitHub API rate limit (5000 req/hour), Azure OpenAI latency <3 seconds
**Scale/Scope**: MVP for individual developers, teams up to 50 users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | Complete spec.md with 4 prioritized user stories, Given-When-Then scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | Following canonical plan-template.md structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear phase boundaries: specify → plan → tasks → implement |
| IV. Test Optionality | ✅ PASS | Tests not explicitly requested in spec - optional for this feature |
| V. Simplicity and DRY | ✅ PASS | Simple architecture: FastAPI + React, no premature abstractions |

## Project Structure

### Documentation (this feature)

```text
specs/001-github-project-chat/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml     # API contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Environment configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User session model
│   │   ├── project.py          # GitHub Project model
│   │   ├── task.py             # Task/item model
│   │   └── chat.py             # Chat message model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github_auth.py      # GitHub OAuth service
│   │   ├── github_projects.py  # GitHub Projects V2 GraphQL
│   │   ├── ai_agent.py         # Azure OpenAI integration
│   │   └── cache.py            # Project list caching
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             # OAuth endpoints
│   │   ├── projects.py         # Project management endpoints
│   │   ├── tasks.py            # Task CRUD endpoints
│   │   └── chat.py             # Chat/AI endpoints
│   └── prompts/
│       └── task_generation.py  # AI prompt templates
└── tests/
    ├── unit/
    └── integration/

frontend/
├── src/
│   ├── main.tsx                # React entry point
│   ├── App.tsx                 # Main app component
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── TaskPreview.tsx
│   │   ├── sidebar/
│   │   │   ├── ProjectSidebar.tsx
│   │   │   ├── ProjectSelector.tsx
│   │   │   └── TaskCard.tsx
│   │   └── auth/
│   │       └── LoginButton.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   └── useChat.ts
│   ├── services/
│   │   └── api.ts              # API client
│   └── types/
│       └── index.ts            # TypeScript types
├── index.html
├── vite.config.ts
└── package.json
```

**Structure Decision**: Web application structure selected (backend/ + frontend/) because the feature requires:
- FastAPI REST API backend for GitHub OAuth handling and GraphQL proxying
- React SPA frontend for interactive chat interface
- Clear separation enables independent deployment and scaling

## Complexity Tracking

> No violations detected - Constitution Check passed for all principles.
