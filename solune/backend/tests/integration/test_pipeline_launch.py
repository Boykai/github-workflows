from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/dev-login",
        json={"github_token": "ghp_test_token"},
    )
    assert response.status_code == 200


async def _select_project(client: AsyncClient, project_id: str) -> None:
    response = await client.post(f"/api/v1/projects/{project_id}/select")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_pipeline_launch_advances_when_backlog_has_no_agents(thin_mock_client: AsyncClient):
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)

    create_response = await thin_mock_client.post(
        f"/api/v1/pipelines/{project_id}",
        json={
            "name": "Ready Only Pipeline",
            "description": "Launches directly into the ready stage",
            "stages": [
                {
                    "id": "stage-ready",
                    "name": "Ready",
                    "order": 0,
                    "execution_mode": "sequential",
                    "groups": [
                        {
                            "id": "group-ready",
                            "order": 0,
                            "execution_mode": "sequential",
                            "agents": [
                                {
                                    "id": "agent-human",
                                    "agent_slug": "human",
                                    "agent_display_name": "Human",
                                    "model_id": "",
                                    "model_name": "",
                                    "tool_ids": [],
                                    "tool_count": 0,
                                    "config": {},
                                }
                            ],
                        }
                    ],
                    "agents": [
                        {
                            "id": "agent-human",
                            "agent_slug": "human",
                            "agent_display_name": "Human",
                            "model_id": "",
                            "model_name": "",
                            "tool_ids": [],
                            "tool_count": 0,
                            "config": {},
                        }
                    ],
                }
            ],
        },
    )
    assert create_response.status_code == 201
    pipeline_id = create_response.json()["id"]

    launch_response = await thin_mock_client.post(
        f"/api/v1/pipelines/{project_id}/launch",
        json={
            "issue_description": "Launch directly into ready review.",
            "pipeline_id": pipeline_id,
        },
    )

    assert launch_response.status_code == 200
    body = launch_response.json()
    assert body["success"] is True
    assert body["current_status"] == "Ready"
    assert body["issue_number"] == 101

    state_response = await thin_mock_client.get("/api/v1/workflow/pipeline-states/101")
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["status"] == "Ready"
    assert state["current_agent"] == "human"
