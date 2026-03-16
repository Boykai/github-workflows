from __future__ import annotations

import json

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.api.webhooks import github_webhook
from src.exceptions import AppException

json_scalar = st.none() | st.booleans() | st.integers() | st.text(max_size=20)
json_value = st.recursive(
    json_scalar,
    lambda children: (
        st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=10), children, max_size=4)
    ),
    max_leaves=10,
)


class FakeRequest:
    def __init__(self, payload: object):
        self._payload = payload

    async def body(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    async def json(self) -> object:
        return self._payload


@pytest.mark.asyncio
@settings(
    max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    event_name=st.text(min_size=1, max_size=20),
    payload=st.dictionaries(st.text(max_size=10), json_value, max_size=6),
)
async def test_github_webhook_dispatch_handles_random_payloads_without_unhandled_exceptions(
    monkeypatch,
    event_name: str,
    payload: dict[str, object],
) -> None:
    monkeypatch.setattr(
        "src.api.webhooks.get_settings",
        lambda: type("S", (), {"github_webhook_secret": "secret"})(),
    )
    monkeypatch.setattr("src.api.webhooks.verify_webhook_signature", lambda *_args: True)

    request = FakeRequest(payload)

    try:
        result = await github_webhook(
            request,
            x_github_event=event_name,
            x_hub_signature_256="sha256=test",
        )
        assert isinstance(result, dict)
    except AppException as exc:
        assert exc.status_code in {400, 401, 422}
