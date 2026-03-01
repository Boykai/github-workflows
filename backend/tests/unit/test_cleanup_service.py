"""Tests for cleanup service (src/services/cleanup_service.py).

Covers the Copilot PR reviewer's minimum test requirements:
- Main-branch protection (preflight and execute)
- Permission enforcement in /execute endpoint
- Invalid project_id / inaccessible board handling
- Fetch failures treated as hard errors (branches & PRs)
- Failures not counted as "preserved"
- Audit log persistence and details JSON parsing
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.cleanup import (
    CleanupExecuteRequest,
    CleanupPreflightRequest,
)
from src.services import cleanup_service

# ── Helpers ─────────────────────────────────────────────────────────


def _make_branch(name: str) -> dict:
    """Create a minimal branch dict as returned by the GitHub REST API."""
    return {"name": name}


def _make_pr(
    number: int,
    title: str = "PR",
    head_branch: str = "feature",
    body: str | None = None,
) -> dict:
    """Create a minimal PR dict as returned by the GitHub REST API."""
    return {
        "number": number,
        "title": title,
        "head": {"ref": head_branch},
        "body": body,
    }


def _make_github_service(
    branches_response=None,
    prs_response=None,
    graphql_response=None,
    permission_response=None,
) -> AsyncMock:
    """Build an AsyncMock of GitHubProjectsService with configurable responses."""
    service = AsyncMock()
    service._build_headers = MagicMock(return_value={"Authorization": "Bearer test"})

    # Default permission: admin access
    if permission_response is None:
        permission_response = MagicMock()
        permission_response.status_code = 200
        permission_response.json.return_value = {"permission": "admin"}

    # Default branches response: empty list (200 OK)
    if branches_response is None:
        branches_response = MagicMock()
        branches_response.status_code = 200
        branches_response.json.return_value = []

    # Default PRs response: empty list (200 OK)
    if prs_response is None:
        prs_response = MagicMock()
        prs_response.status_code = 200
        prs_response.json.return_value = []

    # Default GraphQL: empty board with no items
    if graphql_response is None:
        graphql_response = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [],
                }
            }
        }

    # Route GET requests based on URL content
    async def mock_get(url, headers=None):
        if "/collaborators/" in url:
            return permission_response
        if "/branches" in url:
            return branches_response
        if "/pulls" in url:
            return prs_response
        raise ValueError(f"Unexpected GET URL: {url}")

    service._client = AsyncMock()
    service._client.get = AsyncMock(side_effect=mock_get)
    service._graphql = AsyncMock(return_value=graphql_response)
    service.delete_branch = AsyncMock(return_value=True)

    return service


# ── Main branch protection ──────────────────────────────────────────


class TestMainBranchProtection:
    """Main branch must NEVER be deleted, whether in preflight or execute."""

    async def test_preflight_preserves_main_branch(self):
        """Preflight must always classify 'main' as preserved."""
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = [
            _make_branch("main"),
            _make_branch("stale-branch"),
        ]

        service = _make_github_service(branches_response=branches_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        # main must be in the preserved list, not the delete list
        preserved_names = [b.name for b in result.branches_to_preserve]
        delete_names = [b.name for b in result.branches_to_delete]
        assert "main" in preserved_names
        assert "main" not in delete_names
        # Also verify the preservation reason mentions protection
        main_branch = next(b for b in result.branches_to_preserve if b.name == "main")
        assert "protected" in main_branch.preservation_reason.lower()

    async def test_execute_rejects_main_in_deletion_list(self, mock_db):
        """Execute must refuse to delete main even if it somehow gets included."""
        service = _make_github_service()
        request = CleanupExecuteRequest(
            owner="test",
            repo="repo",
            project_id="PVT_123",
            branches_to_delete=["main", "stale-branch"],
            prs_to_close=[],
        )

        result = await cleanup_service.execute_cleanup(
            service, "token", "test", "repo", request, mock_db, "uid123"
        )

        # main should appear as a failed result, not deleted
        main_results = [r for r in result.results if r.identifier == "main"]
        assert len(main_results) == 1
        assert main_results[0].action == "failed"
        assert "main" in main_results[0].error.lower()

    async def test_execute_api_rejects_main(self, client):
        """The API endpoint itself rejects requests containing 'main'."""
        resp = await client.post(
            "/api/v1/cleanup/execute",
            json={
                "owner": "test",
                "repo": "repo",
                "project_id": "PVT_123",
                "branches_to_delete": ["main"],
                "prs_to_close": [],
            },
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "main" in data["details"]["message"].lower()


# ── Permission enforcement ──────────────────────────────────────────


class TestPermissionEnforcement:
    """Users without push access must be blocked at preflight."""

    async def test_preflight_blocks_read_only_user(self):
        """A user with read-only access should receive has_permission=False."""
        perm_resp = MagicMock()
        perm_resp.status_code = 200
        perm_resp.json.return_value = {"permission": "read"}

        service = _make_github_service(permission_response=perm_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        assert result.has_permission is False
        assert result.permission_error is not None
        assert "push" in result.permission_error.lower()
        # No deletion candidates should be returned
        assert result.branches_to_delete == []
        assert result.prs_to_close == []

    async def test_preflight_allows_admin_user(self):
        """An admin user should pass the permission check."""
        service = _make_github_service()  # default is admin
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        assert result.has_permission is True
        assert result.permission_error is None

    async def test_preflight_handles_permission_api_failure(self):
        """If the permission API returns non-200, block the user."""
        perm_resp = MagicMock()
        perm_resp.status_code = 404

        service = _make_github_service(permission_response=perm_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        assert result.has_permission is False
        assert result.permission_error is not None


# ── Invalid project_id handling ─────────────────────────────────────


class TestInvalidProjectId:
    """Invalid or inaccessible project board must fail the preflight."""

    async def test_preflight_fails_on_invalid_project_id(self):
        """If GraphQL returns no node, preflight should raise RuntimeError."""
        service = _make_github_service(
            graphql_response={"node": None}  # invalid/inaccessible project
        )
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_INVALID")

        with pytest.raises(RuntimeError, match="project_id"):
            await cleanup_service.preflight(service, "token", "testuser", request)

    async def test_preflight_fails_on_empty_graphql_response(self):
        """If GraphQL returns empty dict, preflight should raise RuntimeError."""
        service = _make_github_service(graphql_response={})
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_EMPTY")

        with pytest.raises(RuntimeError, match="project_id"):
            await cleanup_service.preflight(service, "token", "testuser", request)


# ── Fetch failures treated as hard errors ───────────────────────────


class TestFetchFailures:
    """Partial data from fetch failures must abort, not proceed silently."""

    async def test_branch_fetch_failure_raises(self):
        """A non-200 from the branches API should raise RuntimeError."""
        branches_resp = MagicMock()
        branches_resp.status_code = 500

        service = _make_github_service(branches_response=branches_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        with pytest.raises(RuntimeError, match="branches"):
            await cleanup_service.preflight(service, "token", "testuser", request)

    async def test_pr_fetch_failure_raises(self):
        """A non-200 from the PRs API should raise RuntimeError."""
        # Branches succeed, but PRs fail
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = []

        prs_resp = MagicMock()
        prs_resp.status_code = 403

        service = _make_github_service(
            branches_response=branches_resp,
            prs_response=prs_resp,
        )
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        with pytest.raises(RuntimeError, match="pull requests"):
            await cleanup_service.preflight(service, "token", "testuser", request)


# ── Failures not counted as preserved ───────────────────────────────


class TestFailureAccounting:
    """Failed deletions must count as errors, not preserved items."""

    async def test_failed_branch_deletion_counted_correctly(self, mock_db):
        """A branch that fails to delete should be in errors, not preserved count."""
        service = _make_github_service()
        # First branch: succeeds; second branch: fails
        service.delete_branch = AsyncMock(side_effect=[True, False])

        request = CleanupExecuteRequest(
            owner="test",
            repo="repo",
            project_id="PVT_123",
            branches_to_delete=["good-branch", "bad-branch"],
            prs_to_close=[],
        )

        result = await cleanup_service.execute_cleanup(
            service, "token", "test", "repo", request, mock_db, "uid123"
        )

        assert result.branches_deleted == 1
        # branches_preserved in execute response represents failed count
        assert result.branches_preserved == 1
        assert len(result.errors) == 1
        assert result.errors[0].identifier == "bad-branch"
        assert result.errors[0].action == "failed"

    async def test_failed_pr_closure_counted_correctly(self, mock_db):
        """A PR that fails to close should be in errors, not preserved count."""
        service = _make_github_service()

        # PR closure: mock _request_with_retry to return non-200
        error_response = MagicMock()
        error_response.status_code = 422
        error_response.text = "Unprocessable Entity"
        service._request_with_retry = AsyncMock(return_value=error_response)

        request = CleanupExecuteRequest(
            owner="test",
            repo="repo",
            project_id="PVT_123",
            branches_to_delete=[],
            prs_to_close=[42],
        )

        result = await cleanup_service.execute_cleanup(
            service, "token", "test", "repo", request, mock_db, "uid123"
        )

        assert result.prs_closed == 0
        assert result.prs_preserved == 1
        assert len(result.errors) == 1
        assert result.errors[0].identifier == "42"


# ── Audit log persistence and JSON parsing ──────────────────────────


class TestAuditLog:
    """Audit trail must be persisted and details parsed correctly."""

    async def test_audit_log_created_on_execute(self, mock_db):
        """Execute should create an audit log entry in cleanup_audit_logs."""
        service = _make_github_service()
        request = CleanupExecuteRequest(
            owner="test",
            repo="repo",
            project_id="PVT_123",
            branches_to_delete=["stale"],
            prs_to_close=[],
        )

        result = await cleanup_service.execute_cleanup(
            service, "token", "test", "repo", request, mock_db, "uid123"
        )

        # Verify the log was persisted
        cursor = await mock_db.execute(
            "SELECT id, status, details FROM cleanup_audit_logs WHERE id = ?",
            (result.operation_id,),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[1] == "completed"  # status
        # details should be valid JSON
        details = json.loads(row[2])
        assert "results" in details
        assert len(details["results"]) == 1

    async def test_history_returns_parsed_details(self, mock_db):
        """get_cleanup_history should parse the details JSON string into a dict."""
        service = _make_github_service()
        request = CleanupExecuteRequest(
            owner="test",
            repo="repo",
            project_id="PVT_123",
            branches_to_delete=["stale"],
            prs_to_close=[],
        )

        # Execute to create an audit entry
        await cleanup_service.execute_cleanup(
            service, "token", "test", "repo", request, mock_db, "uid123"
        )

        # Fetch history
        history = await cleanup_service.get_cleanup_history(mock_db, "uid123", "test", "repo")

        assert history.count == 1
        op = history.operations[0]
        # details should be a parsed dict, not a raw string
        assert isinstance(op.details, dict)
        assert "results" in op.details

    async def test_history_handles_invalid_json_details(self, mock_db):
        """If details contains invalid JSON, it should be returned as None."""
        # Insert a row with invalid JSON in the details column
        await mock_db.execute(
            """INSERT INTO cleanup_audit_logs
            (id, github_user_id, owner, repo, project_id, started_at,
             completed_at, status, branches_deleted, branches_preserved,
             prs_closed, prs_preserved, errors_count, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "bad-json-id",
                "uid123",
                "test",
                "repo",
                "PVT_123",
                "2026-03-01T00:00:00Z",
                "2026-03-01T00:01:00Z",
                "completed",
                1,
                0,
                0,
                0,
                0,
                "NOT VALID JSON {{{",
            ),
        )
        await mock_db.commit()

        history = await cleanup_service.get_cleanup_history(mock_db, "uid123", "test", "repo")

        # Find the entry with invalid JSON
        bad_entry = next(op for op in history.operations if op.id == "bad-json-id")
        assert bad_entry.details is None


# ── Cross-referencing (issue linkage) ───────────────────────────────


class TestIssueLinkage:
    """Branches/PRs linked to open issues on the board must be preserved."""

    async def test_branch_linked_by_naming_convention_preserved(self):
        """A branch named 'issue-42' should be preserved if issue #42 is open on board."""
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = [
            _make_branch("main"),
            _make_branch("issue-42"),
            _make_branch("stale-experiment"),
        ]

        graphql_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 42,
                                "title": "Fix login bug",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        }
                    ],
                }
            }
        }

        service = _make_github_service(
            branches_response=branches_resp,
            graphql_response=graphql_resp,
        )
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        preserved_names = [b.name for b in result.branches_to_preserve]
        delete_names = [b.name for b in result.branches_to_delete]
        assert "issue-42" in preserved_names
        assert "stale-experiment" in delete_names
        assert result.open_issues_on_board == 1

    async def test_pr_linked_by_body_reference_preserved(self):
        """A PR whose body says 'Closes #42' should be preserved if issue #42 is on board."""
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = [_make_branch("main")]

        prs_resp = MagicMock()
        prs_resp.status_code = 200
        prs_resp.json.return_value = [
            _make_pr(10, "Fix stuff", "feature-a", body="Closes #42"),
            _make_pr(11, "Random PR", "feature-b", body="No issues here"),
        ]

        graphql_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 42,
                                "title": "Fix login bug",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        }
                    ],
                }
            }
        }

        service = _make_github_service(
            branches_response=branches_resp,
            prs_response=prs_resp,
            graphql_response=graphql_resp,
        )
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        preserved_pr_nums = [p.number for p in result.prs_to_preserve]
        close_pr_nums = [p.number for p in result.prs_to_close]
        assert 10 in preserved_pr_nums
        assert 11 in close_pr_nums
