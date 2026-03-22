"""Unit tests for webhook CI failure detection and routing."""

from __future__ import annotations

import pytest

from src.api.webhook_models import (
    CheckRunData,
    CheckRunEvent,
    CheckRunPR,
    CheckSuiteData,
    CheckSuiteEvent,
    OwnerData,
    RepositoryData,
)


class TestCheckRunEventModel:
    """Tests for CheckRunEvent Pydantic model."""

    def test_parse_completed_failure(self):
        """Parse a check_run completed with failure."""
        raw = {
            "action": "completed",
            "check_run": {
                "id": 123,
                "name": "test-suite",
                "status": "completed",
                "conclusion": "failure",
                "head_sha": "abc123",
                "pull_requests": [
                    {
                        "number": 42,
                        "head": {"ref": "feature-branch"},
                        "base": {"ref": "main"},
                    }
                ],
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "owner"},
            },
        }
        event = CheckRunEvent.model_validate(raw)
        assert event.action == "completed"
        assert event.check_run.conclusion == "failure"
        assert event.check_run.name == "test-suite"
        assert len(event.check_run.pull_requests) == 1
        assert event.check_run.pull_requests[0].number == 42

    def test_parse_timed_out(self):
        """Parse a check_run with timed_out conclusion."""
        raw = {
            "action": "completed",
            "check_run": {
                "id": 456,
                "name": "integration-test",
                "status": "completed",
                "conclusion": "timed_out",
                "head_sha": "def456",
                "pull_requests": [],
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "owner"},
            },
        }
        event = CheckRunEvent.model_validate(raw)
        assert event.check_run.conclusion == "timed_out"

    def test_extra_fields_ignored(self):
        """Extra fields should be ignored (ConfigDict extra='ignore')."""
        raw = {
            "action": "completed",
            "check_run": {
                "id": 789,
                "name": "test",
                "status": "completed",
                "conclusion": "success",
                "head_sha": "ghi789",
                "pull_requests": [],
                "extra_field": "should be ignored",
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "owner"},
                "extra": True,
            },
            "sender": {"login": "user"},
        }
        event = CheckRunEvent.model_validate(raw)
        assert event.action == "completed"


class TestCheckSuiteEventModel:
    """Tests for CheckSuiteEvent Pydantic model."""

    def test_parse_completed_failure(self):
        """Parse a check_suite completed with failure."""
        raw = {
            "action": "completed",
            "check_suite": {
                "id": 100,
                "status": "completed",
                "conclusion": "failure",
                "head_sha": "abc123",
                "pull_requests": [
                    {
                        "number": 99,
                        "head": {"ref": "fix-branch"},
                        "base": {"ref": "main"},
                    }
                ],
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "owner"},
            },
        }
        event = CheckSuiteEvent.model_validate(raw)
        assert event.action == "completed"
        assert event.check_suite.conclusion == "failure"
        assert len(event.check_suite.pull_requests) == 1

    def test_parse_success(self):
        """Parse a check_suite with success conclusion."""
        raw = {
            "action": "completed",
            "check_suite": {
                "id": 200,
                "status": "completed",
                "conclusion": "success",
                "head_sha": "def456",
                "pull_requests": [],
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "owner"},
            },
        }
        event = CheckSuiteEvent.model_validate(raw)
        assert event.check_suite.conclusion == "success"


class TestWebhookRouting:
    """Tests for check_run/check_suite webhook handler routing logic."""

    @pytest.mark.asyncio
    async def test_check_run_failure_processed(self):
        """check_run with failure conclusion should be processed."""
        from src.api.webhooks import handle_check_run_event

        event = CheckRunEvent(
            action="completed",
            check_run=CheckRunData(
                id=1,
                name="test-ci",
                status="completed",
                conclusion="failure",
                head_sha="abc123",
                pull_requests=[
                    CheckRunPR(number=42),
                ],
            ),
            repository=RepositoryData(
                name="repo",
                owner=OwnerData(login="owner"),
            ),
        )
        result = await handle_check_run_event(event)
        assert result["status"] == "processed"
        assert result["event"] == "check_run_failure"
        assert 42 in result["pr_numbers"]

    @pytest.mark.asyncio
    async def test_check_run_timed_out_processed(self):
        """check_run with timed_out conclusion should be processed."""
        from src.api.webhooks import handle_check_run_event

        event = CheckRunEvent(
            action="completed",
            check_run=CheckRunData(
                id=2,
                name="slow-test",
                status="completed",
                conclusion="timed_out",
                head_sha="def456",
                pull_requests=[CheckRunPR(number=99)],
            ),
            repository=RepositoryData(
                name="repo",
                owner=OwnerData(login="owner"),
            ),
        )
        result = await handle_check_run_event(event)
        assert result["status"] == "processed"
        assert result["conclusion"] == "timed_out"

    @pytest.mark.asyncio
    async def test_check_run_success_ignored(self):
        """check_run with success conclusion should be ignored."""
        from src.api.webhooks import handle_check_run_event

        event = CheckRunEvent(
            action="completed",
            check_run=CheckRunData(
                id=3,
                name="test",
                status="completed",
                conclusion="success",
                head_sha="ghi789",
                pull_requests=[CheckRunPR(number=1)],
            ),
            repository=RepositoryData(
                name="repo",
                owner=OwnerData(login="owner"),
            ),
        )
        result = await handle_check_run_event(event)
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_check_run_non_completed_ignored(self):
        """check_run with non-completed action should be ignored."""
        from src.api.webhooks import handle_check_run_event

        event = CheckRunEvent(
            action="created",
            check_run=CheckRunData(
                id=4,
                name="test",
                status="queued",
                head_sha="jkl012",
                pull_requests=[],
            ),
            repository=RepositoryData(
                name="repo",
                owner=OwnerData(login="owner"),
            ),
        )
        result = await handle_check_run_event(event)
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_check_suite_failure_processed(self):
        """check_suite with failure conclusion should be processed."""
        from src.api.webhooks import handle_check_suite_event

        event = CheckSuiteEvent(
            action="completed",
            check_suite=CheckSuiteData(
                id=10,
                status="completed",
                conclusion="failure",
                head_sha="abc123",
                pull_requests=[CheckRunPR(number=55)],
            ),
            repository=RepositoryData(
                name="repo",
                owner=OwnerData(login="owner"),
            ),
        )
        result = await handle_check_suite_event(event)
        assert result["status"] == "processed"
        assert result["event"] == "check_suite_failure"

    @pytest.mark.asyncio
    async def test_check_suite_success_ignored(self):
        """check_suite with success conclusion should be ignored."""
        from src.api.webhooks import handle_check_suite_event

        event = CheckSuiteEvent(
            action="completed",
            check_suite=CheckSuiteData(
                id=20,
                status="completed",
                conclusion="success",
                head_sha="def456",
                pull_requests=[CheckRunPR(number=1)],
            ),
            repository=RepositoryData(
                name="repo",
                owner=OwnerData(login="owner"),
            ),
        )
        result = await handle_check_suite_event(event)
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_check_suite_no_prs_ignored(self):
        """check_suite with no associated PRs should be ignored."""
        from src.api.webhooks import handle_check_suite_event

        event = CheckSuiteEvent(
            action="completed",
            check_suite=CheckSuiteData(
                id=30,
                status="completed",
                conclusion="failure",
                head_sha="ghi789",
                pull_requests=[],
            ),
            repository=RepositoryData(
                name="repo",
                owner=OwnerData(login="owner"),
            ),
        )
        result = await handle_check_suite_event(event)
        assert result["status"] == "ignored"
        assert result["reason"] == "no_associated_prs"
