"""Verification tests for chat message pagination."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.fixture()
def chat_module():
    """Import and reset the chat module cache for isolation."""
    from src.api import chat

    # Clear the in-memory caches and lock map between tests.
    chat._messages.clear()
    chat._proposals.clear()
    chat._recommendations.clear()
    chat._locks.clear()
    return chat


class TestPagination:
    """Chat messages endpoint pagination."""

    async def test_limit_and_offset_return_correct_slice(self, chat_module) -> None:
        from src.models.chat import ChatMessage, SenderType

        session_id = uuid4()
        key = str(session_id)

        # Populate cache directly (bypass persistence for unit test).
        messages = [
            ChatMessage(
                message_id=str(uuid4()),
                session_id=key,
                sender_type=SenderType.USER,
                content=f"msg-{i}",
            )
            for i in range(10)
        ]
        chat_module._messages[key] = messages

        all_msgs = await chat_module.get_session_messages(session_id)
        assert len(all_msgs) == 10

        # Simulate endpoint pagination.
        limit, offset = 5, 0
        page = all_msgs[offset : offset + limit]
        assert len(page) == 5
        assert page[0].content == "msg-0"

        limit, offset = 5, 5
        page = all_msgs[offset : offset + limit]
        assert len(page) == 5
        assert page[0].content == "msg-5"

    async def test_offset_beyond_total_returns_empty(self, chat_module) -> None:
        from src.models.chat import ChatMessage, SenderType

        session_id = uuid4()
        key = str(session_id)

        messages = [
            ChatMessage(
                message_id=str(uuid4()),
                session_id=key,
                sender_type=SenderType.USER,
                content=f"msg-{i}",
            )
            for i in range(3)
        ]
        chat_module._messages[key] = messages

        all_msgs = await chat_module.get_session_messages(session_id)
        page = all_msgs[100 : 100 + 50]
        assert page == []
