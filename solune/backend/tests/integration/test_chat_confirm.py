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
async def test_chat_confirm_creates_issue_and_starts_selected_pipeline(
    thin_mock_client: AsyncClient,
):
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)

    create_response = await thin_mock_client.post(
        f"/api/v1/pipelines/{project_id}",
        json={
            "name": "Backlog Human Pipeline",
            "description": "Assigns a human immediately from backlog",
            "stages": [
                {
                    "id": "stage-backlog",
                    "name": "Backlog",
                    "order": 0,
                    "execution_mode": "sequential",
                    "groups": [
                        {
                            "id": "group-backlog",
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

    proposal_response = await thin_mock_client.post(
        "/api/v1/chat/messages",
        json={
            "content": "Create a task for end-to-end confirm coverage.",
            "ai_enhance": False,
            "pipeline_id": pipeline_id,
        },
    )
    assert proposal_response.status_code == 200
    proposal_body = proposal_response.json()
    assert proposal_body["action_type"] == "task_create"
    proposal_id = proposal_body["action_data"]["proposal_id"]

    confirm_response = await thin_mock_client.post(
        f"/api/v1/chat/proposals/{proposal_id}/confirm",
        json={},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["pipeline_source"] == "pipeline"
    assert confirmed["pipeline_name"] == "Backlog Human Pipeline"

    state_response = await thin_mock_client.get("/api/v1/workflow/pipeline-states/101")
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["status"] == "Backlog"
    assert state["current_agent"] == "human"

    messages_response = await thin_mock_client.get("/api/v1/chat/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()["messages"]
    assert any("Issue created" in message["content"] for message in messages)
