from __future__ import annotations

import json

import pytest

from src.services import signal_bridge


@pytest.mark.asyncio
async def test_ws_listener_logs_sender_timestamp_and_preview_on_processing_error(
    monkeypatch,
    caplog,
) -> None:
    class FakeWebSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def __aiter__(self):
            payload = {
                "envelope": {
                    "source": "+15551234567",
                    "timestamp": 1700000000,
                    "syncMessage": {
                        "sentMessage": {
                            "message": "hello from signal",
                            "destinationNumber": "+15551234567",
                        }
                    },
                }
            }
            return _SingleMessageIterator(json.dumps(payload))

    class _SingleMessageIterator:
        def __init__(self, message: str):
            self._message = message
            self._sent = False

        async def __anext__(self):
            if self._sent:
                raise asyncio.CancelledError()
            self._sent = True
            return self._message

    import asyncio

    async def fake_process(_: dict) -> None:
        raise RuntimeError("processing failed")

    monkeypatch.setattr(
        signal_bridge.websockets, "connect", lambda *args, **kwargs: FakeWebSocket()
    )
    monkeypatch.setattr(signal_bridge, "_process_inbound_ws_message", fake_process)

    with caplog.at_level("ERROR"):
        await signal_bridge._ws_listen_loop("+15551234567")

    assert "+15551234567" in caplog.text
    assert "1700000000" in caplog.text
    assert "hello from signal" in caplog.text
    assert "processing failed" in caplog.text
