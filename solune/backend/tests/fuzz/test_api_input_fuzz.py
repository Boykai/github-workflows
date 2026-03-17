from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

json_scalar = st.none() | st.booleans() | st.integers() | st.text(max_size=20)
json_value = st.recursive(
    json_scalar,
    lambda children: (
        st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=10), children, max_size=4)
    ),
    max_leaves=10,
)


@pytest.mark.asyncio
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(payload=st.dictionaries(st.text(max_size=12), json_value, max_size=8))
async def test_create_app_endpoint_handles_random_payloads_without_500(
    client,
    mock_github_service,
    payload: dict[str, object],
) -> None:
    mock_github_service.get_branch_head_oid.return_value = None

    response = await client.post("/api/v1/apps", json=payload)

    assert response.status_code in {201, 400, 401, 409, 422}


@pytest.mark.asyncio
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(payload=st.dictionaries(st.text(max_size=12), json_value, max_size=8))
async def test_update_app_endpoint_handles_random_payloads_without_500(
    client,
    payload: dict[str, object],
) -> None:
    response = await client.put("/api/v1/apps/non-existent-app", json=payload)

    assert response.status_code in {400, 401, 404, 422}
