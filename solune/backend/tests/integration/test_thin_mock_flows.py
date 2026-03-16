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
async def test_project_selection_then_board_fetch_uses_real_http_layer(
    thin_mock_client: AsyncClient,
):
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)

    me_response = await thin_mock_client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["selected_project_id"] == project_id

    board_response = await thin_mock_client.get(f"/api/v1/board/projects/{project_id}")
    assert board_response.status_code == 200
    body = board_response.json()
    assert body["project"]["project_id"] == project_id
    assert body["columns"][0]["items"][0]["title"] == "Existing backlog task"


@pytest.mark.asyncio
async def test_chat_message_send_round_trips_through_persistence(thin_mock_client: AsyncClient):
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)

    send_response = await thin_mock_client.post(
        "/api/v1/chat/messages",
        json={"content": "Create a task for smoke coverage", "ai_enhance": False},
    )
    assert send_response.status_code == 200
    assert send_response.json()["action_type"] == "task_create"
    assert "Generated task title" in send_response.json()["content"]

    messages_response = await thin_mock_client.get("/api/v1/chat/messages")
    assert messages_response.status_code == 200
    body = messages_response.json()
    assert body["total"] == 2
    assert [message["sender_type"] for message in body["messages"]] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_pipeline_launch_then_state_query_returns_active_human_step(
    thin_mock_client: AsyncClient,
):
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)

    create_response = await thin_mock_client.post(
        f"/api/v1/pipelines/{project_id}",
        json={
            "name": "Human Backlog Pipeline",
            "description": "Single human backlog stage",
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

    launch_response = await thin_mock_client.post(
        f"/api/v1/pipelines/{project_id}/launch",
        json={
            "issue_description": "# Human review\n\nVerify the launch path end to end.",
            "pipeline_id": pipeline_id,
        },
    )
    assert launch_response.status_code == 200
    launch_body = launch_response.json()
    assert launch_body["success"] is True
    assert launch_body["issue_number"] == 101

    state_response = await thin_mock_client.get("/api/v1/workflow/pipeline-states/101")
    assert state_response.status_code == 200
    state_body = state_response.json()
    assert state_body["project_id"] == project_id
    assert state_body["status"] == "Backlog"
    assert state_body["current_agent"] == "human"
    assert state_body["completed_agents"] == []
