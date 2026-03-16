from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.api.webhook_models import PullRequestEvent
from src.services import pipeline_state_store
from src.services.workflow_orchestrator.models import PipelineState


@pytest.mark.asyncio
async def test_pipeline_state_round_trips_nested_untyped_shapes(mock_db) -> None:
    issue_number = 1201
    await pipeline_state_store.init_pipeline_state_store(mock_db)
    pipeline_state_store._pipeline_states.clear()

    state = PipelineState(
        issue_number=issue_number,
        project_id="PVT_roundtrip",
        status="running",
        agents=["planner", "builder"],
        current_agent_index=1,
        completed_agents=["planner"],
        started_at=datetime.now(UTC),
        error=None,
        agent_sub_issues={
            "builder": {
                "number": 44,
                "node_id": "node-44",
                "url": "https://example.test/issues/44",
                "extra": {"nested": [None, {"unicode_key_ß": "ok"}]},
            }
        },
        parallel_agent_statuses={"planner": "completed", "builder": "running"},
    )

    await pipeline_state_store.set_pipeline_state(issue_number, state)
    restored = await pipeline_state_store.get_pipeline_state_async(issue_number)

    assert restored is not None
    assert restored.agent_sub_issues["builder"]["number"] == 44
    assert restored.parallel_agent_statuses == {"planner": "completed", "builder": "running"}


def test_pull_request_event_round_trips_and_rejects_missing_required_fields() -> None:
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 77,
            "draft": False,
            "user": {"login": "copilot-swe-agent[bot]"},
            "head": {"ref": "issue-77-branch"},
            "body": "Fixes #77 with unicode ✓",
        },
        "repository": {
            "name": "solune",
            "owner": {"login": "Boykai"},
        },
    }

    model = PullRequestEvent.model_validate(payload)
    dumped = model.model_dump()

    assert dumped["pull_request"]["number"] == 77
    assert dumped["pull_request"]["head"]["ref"] == "issue-77-branch"
    assert dumped["repository"]["owner"]["login"] == "Boykai"

    with pytest.raises(ValidationError):
        PullRequestEvent.model_validate(
            {
                "action": "opened",
                "pull_request": {"draft": False, "user": {"login": "copilot"}},
                "repository": {"name": "solune", "owner": {"login": "Boykai"}},
            }
        )
