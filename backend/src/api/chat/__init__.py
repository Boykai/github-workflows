"""Chat API package — aggregates messaging, proposal, and upload routes."""

from __future__ import annotations

from fastapi import APIRouter

# Re-export shared state for backward compatibility with external callers
# (api/__init__.py, services/signal_chat.py, services/signal_bridge.py, api/workflow.py)
from src.api.chat._state import (  # noqa: F401
    _messages,
    _proposals,
    _recommendations,
    add_message,
    get_session_messages,
)
from src.api.chat.messaging import router as messaging_router
from src.api.chat.proposals import router as proposals_router
from src.api.chat.uploads import router as uploads_router

router = APIRouter()
router.include_router(messaging_router)
router.include_router(proposals_router)
router.include_router(uploads_router)
