# Contract: Chat Module API (Post-Decomposition)

**Feature**: 038-code-quality-overhaul | **Status**: Draft

## Purpose

Define the API surface of the decomposed `api/chat/` package. Currently `api/chat.py` is a single 1,080-line file with 14 functions across 5 responsibilities. After decomposition it becomes a package with focused submodules.

## Module Structure

```
backend/src/api/chat/
├── __init__.py          # Re-exports the router
├── messaging.py         # Core send/receive (WebSocket + HTTP fallback)
├── commands.py          # Slash commands (/assign, /status, /label, etc.)
├── proposals.py         # Proposal CRUD (confirm, cancel, list)
└── uploads.py           # File attachment handling
```

## Router Composition

### `__init__.py`

```python
from fastapi import APIRouter
from .messaging import router as messaging_router
from .commands import router as commands_router
from .proposals import router as proposals_router
from .uploads import router as uploads_router

router = APIRouter(prefix="/chat", tags=["chat"])
router.include_router(messaging_router)
router.include_router(commands_router)
router.include_router(proposals_router)
router.include_router(uploads_router)
```

### Endpoint Distribution

| Endpoint | Method | Module | Description |
|----------|--------|--------|-------------|
| `/chat/send` | POST | messaging | Send user message, get AI response |
| `/chat/ws` | WS | messaging | WebSocket for streaming responses |
| `/chat/history` | GET | messaging | Retrieve chat history for session |
| `/chat/clear` | DELETE | messaging | Clear session chat history |
| `/chat/command` | POST | commands | Execute a slash command |
| `/chat/commands` | GET | commands | List available commands |
| `/chat/proposals` | GET | proposals | List pending proposals for session |
| `/chat/proposals/{id}/confirm` | POST | proposals | Confirm a proposal |
| `/chat/proposals/{id}/cancel` | POST | proposals | Cancel a proposal |
| `/chat/upload` | POST | uploads | Upload file attachment |

## Shared Dependencies

All submodules import from these shared locations (no cross-submodule imports):

- `utils.resolve_repository()` — canonical repository resolution (replaces duplicate `_resolve_repository()`)
- `dependencies.require_selected_project()` — project context injection
- `logging_utils.handle_service_error()` — error handling wrapper
- `services.chat_store` — persistence layer (currently dead, to be wired)

## Persistence Integration

### Write-Through Strategy (3-Phase)

**Phase A** — Write-through: `chat_store.save_message()` called after every send/receive. In-memory dict remains the read path.

**Phase B** — Read cutover: `chat_store.get_messages()` becomes the read path. In-memory dict removed.

**Phase C** — Cleanup: Remove in-memory fallback code. `chat_store` is the sole persistence layer.

### chat_store API (existing, currently unwired)

```python
# services/chat_store.py — already implemented
async def save_message(session_id: str, sender: str, content: str, metadata: dict | None = None) -> None: ...
async def get_messages(session_id: str) -> list[dict]: ...
async def clear_messages(session_id: str) -> None: ...
async def save_proposal(session_id: str, proposal: dict) -> str: ...
async def get_proposals(session_id: str) -> list[dict]: ...
async def update_proposal_status(proposal_id: str, status: str) -> None: ...
async def save_recommendation(session_id: str, recommendation: dict) -> str: ...
async def get_recommendations(session_id: str) -> list[dict]: ...
async def update_recommendation_status(recommendation_id: str, status: str) -> None: ...
```
