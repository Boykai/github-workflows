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
from src.services.cleanup_service import (
    _collect_all_referenced_issues,
    _extract_issue_numbers_from_branch,
    _extract_issue_numbers_from_text,
    _is_solune_owned_branch,
    _is_solune_owned_pr,
    _references_app_created_issue,
)

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
    issues_response=None,
) -> AsyncMock:
    """Build an AsyncMock of GitHubProjectsService with configurable responses."""
    service = AsyncMock()

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

    # Default issues response: empty list (200 OK)
    if issues_response is None:
        issues_response = MagicMock()
        issues_response.status_code = 200
        issues_response.json.return_value = []

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

    # Route _rest_response calls based on path content
    async def mock_rest_response(access_token, method, path, **kwargs):
        if "/collaborators/" in path:
            return permission_response
        if "/branches" in path:
            return branches_response
        if "/pulls" in path:
            return prs_response
        if "/issues" in path:
            return issues_response
        raise ValueError(f"Unexpected _rest_response path: {method} {path}")

    service._rest_response = AsyncMock(side_effect=mock_rest_response)
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

        # PR closure: mock _rest_response to return non-200
        error_response = MagicMock()
        error_response.status_code = 422
        error_response.text = "Unprocessable Entity"
        service._rest_response = AsyncMock(return_value=error_response)

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

    async def test_preflight_deletes_all_unlinked_branches(self):
        """All unlinked branches (Solune-owned or not) are eligible for deletion."""
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = [
            _make_branch("main"),
            _make_branch("feature/manual-experiment"),
            _make_branch("agent/stale-helper"),
        ]

        service = _make_github_service(branches_response=branches_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        delete_names = [b.name for b in result.branches_to_delete]
        preserved_names = [b.name for b in result.branches_to_preserve]

        assert "agent/stale-helper" in delete_names
        assert "feature/manual-experiment" in delete_names
        assert "main" in preserved_names
        assert "main" not in delete_names

    async def test_preflight_closes_all_unlinked_prs(self):
        """All unlinked PRs (Solune-owned or not) are eligible for closure."""
        prs_resp = MagicMock()
        prs_resp.status_code = 200
        prs_resp.json.return_value = [
            _make_pr(
                10, "Manual cleanup candidate", "feature/manual-experiment", body="No issue link"
            ),
            _make_pr(
                11, "Update agent: Judge", "agent/update-judge", body="## Update Agent: Judge"
            ),
        ]

        service = _make_github_service(prs_response=prs_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        close_pr_nums = [p.number for p in result.prs_to_close]

        assert 11 in close_pr_nums
        assert 10 in close_pr_nums

    async def test_preflight_deletes_prs_with_generic_title(self):
        """A PR with a generic title and no board link is eligible for deletion."""
        prs_resp = MagicMock()
        prs_resp.status_code = 200
        prs_resp.json.return_value = [
            _make_pr(
                12,
                "Chore: update dependencies",
                "feature/dependency-refresh",
                body="Manual maintenance follow-up",
            ),
        ]

        service = _make_github_service(prs_response=prs_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        close_pr_nums = [p.number for p in result.prs_to_close]

        assert 12 in close_pr_nums


# ── Orphaned Issues ────────────────────────────────────────────────


class TestOrphanedIssues:
    """Tests for orphaned app-created issue detection and cleanup."""

    async def test_preflight_detects_orphaned_issues(self):
        """An app-created issue NOT on the board should appear in orphaned_issues."""
        issues_resp = MagicMock()
        issues_resp.status_code = 200
        issues_resp.json.return_value = [
            {
                "number": 100,
                "title": "Orphan task",
                "labels": [{"name": "ai-generated"}],
                "html_url": "https://github.com/test/repo/issues/100",
            },
        ]

        # Board has issue #42, but NOT #100
        graphql_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 42,
                                "title": "Board issue",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        }
                    ],
                }
            }
        }

        service = _make_github_service(
            graphql_response=graphql_resp,
            issues_response=issues_resp,
        )
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        assert len(result.orphaned_issues) == 1
        assert result.orphaned_issues[0].number == 100
        assert result.orphaned_issues[0].title == "Orphan task"
        assert "ai-generated" in result.orphaned_issues[0].labels

    async def test_preflight_excludes_board_issues_from_orphans(self):
        """An app-created issue that IS on the board should NOT be orphaned."""
        issues_resp = MagicMock()
        issues_resp.status_code = 200
        issues_resp.json.return_value = [
            {
                "number": 42,
                "title": "Board issue",
                "labels": [{"name": "chore"}],
                "html_url": "https://github.com/test/repo/issues/42",
            },
        ]

        graphql_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 42,
                                "title": "Board issue",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        }
                    ],
                }
            }
        }

        service = _make_github_service(
            graphql_response=graphql_resp,
            issues_response=issues_resp,
        )
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        assert len(result.orphaned_issues) == 0

    async def test_preflight_skips_pull_requests_in_issues_response(self):
        """The /issues endpoint also returns PRs; they should be filtered out."""
        issues_resp = MagicMock()
        issues_resp.status_code = 200
        issues_resp.json.return_value = [
            {
                "number": 200,
                "title": "A PR, not an issue",
                "labels": [{"name": "ai-generated"}],
                "pull_request": {"url": "https://api.github.com/repos/test/repo/pulls/200"},
            },
            {
                "number": 201,
                "title": "Real orphaned issue",
                "labels": [{"name": "ai-generated"}],
                "html_url": "https://github.com/test/repo/issues/201",
            },
        ]

        service = _make_github_service(issues_response=issues_resp)
        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")

        result = await cleanup_service.preflight(service, "token", "testuser", request)

        orphan_numbers = [o.number for o in result.orphaned_issues]
        assert 200 not in orphan_numbers
        assert 201 in orphan_numbers

    async def test_execute_closes_orphaned_issues(self):
        """Execute should close issues listed in issues_to_close."""
        service = _make_github_service()

        close_response = MagicMock()
        close_response.status_code = 200
        close_response.json.return_value = {"number": 100, "state": "closed"}
        service._rest_response = AsyncMock(return_value=close_response)

        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()

        request = CleanupExecuteRequest(
            owner="test",
            repo="repo",
            project_id="PVT_123",
            branches_to_delete=[],
            prs_to_close=[],
            issues_to_close=[100, 101],
        )

        result = await cleanup_service.execute_cleanup(
            service, "token", "test", "repo", request, db, "user123"
        )

        assert result.issues_closed == 2
        issue_results = [r for r in result.results if r.item_type == "issue"]
        assert len(issue_results) == 2
        assert all(r.action == "closed" for r in issue_results)

    async def test_execute_handles_issue_close_failure(self):
        """Failed issue closure should be recorded as an error, not crash."""
        service = _make_github_service()

        fail_response = MagicMock()
        fail_response.status_code = 404
        fail_response.text = "Not Found"
        service._rest_response = AsyncMock(return_value=fail_response)

        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()

        request = CleanupExecuteRequest(
            owner="test",
            repo="repo",
            project_id="PVT_123",
            branches_to_delete=[],
            prs_to_close=[],
            issues_to_close=[999],
        )

        result = await cleanup_service.execute_cleanup(
            service, "token", "test", "repo", request, db, "user123"
        )

        assert result.issues_closed == 0
        assert len(result.errors) == 1
        assert result.errors[0].item_type == "issue"
        assert result.errors[0].action == "failed"


# =============================================================================
# Pure helper function tests (T102)
# =============================================================================


class TestExtractIssueNumbersFromBranch:
    """_extract_issue_numbers_from_branch parses issue numbers from branch names."""

    def test_issue_prefix(self):
        assert _extract_issue_numbers_from_branch("issue-42") == [42]

    def test_issue_prefix_no_dash(self):
        assert _extract_issue_numbers_from_branch("issue42") == [42]

    def test_numeric_prefix(self):
        assert _extract_issue_numbers_from_branch("42-add-feature") == [42]

    def test_fix_prefix(self):
        assert _extract_issue_numbers_from_branch("fix/123") == [123]

    def test_feature_prefix(self):
        assert _extract_issue_numbers_from_branch("feature-99") == [99]

    def test_no_match(self):
        assert _extract_issue_numbers_from_branch("main") == []

    def test_empty_string(self):
        assert _extract_issue_numbers_from_branch("") == []

    def test_resolve_prefix(self):
        assert _extract_issue_numbers_from_branch("resolve/7") == [7]


class TestExtractIssueNumbersFromText:
    """_extract_issue_numbers_from_text parses issue refs from PR body text."""

    def test_closes_reference(self):
        assert sorted(_extract_issue_numbers_from_text("Closes #42")) == [42]

    def test_fixes_reference(self):
        assert sorted(_extract_issue_numbers_from_text("Fixes #10")) == [10]

    def test_multiple_references(self):
        nums = sorted(_extract_issue_numbers_from_text("Closes #5, Fixes #10, also #20"))
        assert nums == [5, 10, 20]

    def test_hash_only(self):
        assert sorted(_extract_issue_numbers_from_text("see #99")) == [99]

    def test_empty_text(self):
        assert _extract_issue_numbers_from_text("") == []

    def test_no_references(self):
        assert _extract_issue_numbers_from_text("just some text") == []

    def test_deduplication(self):
        nums = _extract_issue_numbers_from_text("Closes #5 and also fixes #5")
        assert nums == [5]


class TestReferencesAppCreatedIssue:
    """_references_app_created_issue checks set membership."""

    def test_match(self):
        assert _references_app_created_issue([5, 10], {5, 20}) is True

    def test_no_match(self):
        assert _references_app_created_issue([5, 10], {20, 30}) is False

    def test_empty_issue_numbers(self):
        assert _references_app_created_issue([], {5}) is False

    def test_empty_app_numbers(self):
        assert _references_app_created_issue([5], set()) is False


class TestIsSoluneOwnedPr:
    """_is_solune_owned_pr classifies PRs via branch, body markers, and issue refs."""

    def test_owned_branch_prefix_agent(self):
        pr = {"head": {"ref": "agent/fix-123"}, "title": "", "body": ""}
        assert _is_solune_owned_pr(pr, set()) is True

    def test_owned_branch_prefix_chore(self):
        pr = {"head": {"ref": "chore/update-deps"}, "title": "", "body": ""}
        assert _is_solune_owned_pr(pr, set()) is True

    def test_body_marker(self):
        pr = {
            "head": {"ref": "main"},
            "title": "",
            "body": "_auto-generated by chores feature._",
        }
        assert _is_solune_owned_pr(pr, set()) is True

    def test_references_app_issue_in_body(self):
        pr = {"head": {"ref": "main"}, "title": "", "body": "Fixes #5"}
        assert _is_solune_owned_pr(pr, {5}) is True

    def test_title_alone_insufficient(self):
        pr = {"head": {"ref": "main"}, "title": "add agent: foo", "body": "normal text"}
        assert _is_solune_owned_pr(pr, set()) is False

    def test_unrelated_pr(self):
        pr = {"head": {"ref": "feature-x"}, "title": "Add feature", "body": "Description"}
        assert _is_solune_owned_pr(pr, set()) is False

    def test_references_app_issue_in_branch(self):
        pr = {"head": {"ref": "issue-5"}, "title": "", "body": ""}
        assert _is_solune_owned_pr(pr, {5}) is True


class TestIsSoluneOwnedBranch:
    """_is_solune_owned_branch classifies branches via prefix, issues, and PRs."""

    def test_agent_prefix(self):
        assert _is_solune_owned_branch("agent/cleanup", [], set()) is True

    def test_chore_prefix(self):
        assert _is_solune_owned_branch("chore/update", [], set()) is True

    def test_references_app_issue(self):
        assert _is_solune_owned_branch("issue-42", [], {42}) is True

    def test_associated_pr_is_owned(self):
        pr = {
            "head": {"ref": "feature-x"},
            "title": "",
            "body": "_auto-generated by chores feature._",
        }
        assert _is_solune_owned_branch("feature-x", [pr], set()) is True

    def test_unrelated_branch(self):
        assert _is_solune_owned_branch("feature-x", [], set()) is False

    def test_pr_for_different_branch(self):
        pr = {
            "head": {"ref": "other-branch"},
            "title": "",
            "body": "_auto-generated by chores feature._",
        }
        assert _is_solune_owned_branch("feature-x", [pr], set()) is False


# ── _collect_all_referenced_issues helper ───────────────────────────


class TestCollectAllReferencedIssues:
    """_collect_all_referenced_issues gathers issue numbers from branches & PRs."""

    def test_branch_name_references(self):
        branches = [_make_branch("issue-10"), _make_branch("42-feature")]
        result = _collect_all_referenced_issues(branches, [])
        assert 10 in result
        assert 42 in result

    def test_pr_body_references(self):
        prs = [_make_pr(1, body="Closes #55 and fixes #66")]
        result = _collect_all_referenced_issues([], prs)
        assert 55 in result
        assert 66 in result

    def test_pr_head_branch_references(self):
        prs = [_make_pr(1, head_branch="issue-99")]
        result = _collect_all_referenced_issues([], prs)
        assert 99 in result

    def test_deduplication(self):
        branches = [_make_branch("issue-5")]
        prs = [_make_pr(1, body="Fixes #5")]
        result = _collect_all_referenced_issues(branches, prs)
        assert result == {5}

    def test_empty_inputs(self):
        assert _collect_all_referenced_issues([], []) == set()


# ── Orphan-by-parent detection ──────────────────────────────────────


class TestOrphanByParent:
    """When a parent issue is no longer on the board, child items are orphaned."""

    async def test_branch_orphaned_when_parent_not_on_board(self):
        """A non-Solune branch referencing a sub-issue whose parent is gone is orphaned."""
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = [
            _make_branch("main"),
            _make_branch("issue-50"),  # References sub-issue #50
        ]

        # Board has no parent #100 — only sub-issue #50
        board_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 50,
                                "title": "Sub-issue",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        },
                    ],
                }
            }
        }
        # Parent query: issue #50 has parent #100 which is NOT on the board
        parent_resp = {
            "repository": {
                "i_50": {"parent": {"number": 100, "state": "CLOSED", "title": "Parent task"}},
            }
        }

        service = _make_github_service(branches_response=branches_resp)
        service._graphql = AsyncMock(side_effect=[board_resp, parent_resp])

        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")
        result = await cleanup_service.preflight(service, "token", "testuser", request)

        delete_names = [b.name for b in result.branches_to_delete]
        assert "issue-50" in delete_names
        deleted_branch = next(b for b in result.branches_to_delete if b.name == "issue-50")
        assert "no longer on the project board" in deleted_branch.deletion_reason
        assert "#100" in deleted_branch.deletion_reason

    async def test_pr_orphaned_when_parent_not_on_board(self):
        """A PR referencing a sub-issue whose parent is gone is orphaned."""
        prs_resp = MagicMock()
        prs_resp.status_code = 200
        prs_resp.json.return_value = [
            _make_pr(10, "Fix stuff", "feature-x", body="Closes #50"),
        ]

        board_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 50,
                                "title": "Sub-issue",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        },
                    ],
                }
            }
        }
        parent_resp = {
            "repository": {
                "i_50": {"parent": {"number": 100, "state": "CLOSED", "title": "Parent task"}},
            }
        }

        service = _make_github_service(prs_response=prs_resp)
        service._graphql = AsyncMock(side_effect=[board_resp, parent_resp])

        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")
        result = await cleanup_service.preflight(service, "token", "testuser", request)

        close_nums = [p.number for p in result.prs_to_close]
        assert 10 in close_nums
        closed_pr = next(p for p in result.prs_to_close if p.number == 10)
        assert "no longer on the project board" in closed_pr.deletion_reason

    async def test_board_issue_orphaned_when_parent_not_on_board(self):
        """A board issue whose parent is not on the board appears in orphaned_issues."""
        board_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 50,
                                "title": "Sub-issue",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        },
                    ],
                }
            }
        }
        parent_resp = {
            "repository": {
                "i_50": {"parent": {"number": 100, "state": "CLOSED", "title": "Parent task"}},
            }
        }

        service = _make_github_service()
        service._graphql = AsyncMock(side_effect=[board_resp, parent_resp])

        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")
        result = await cleanup_service.preflight(service, "token", "testuser", request)

        orphan_nums = [o.number for o in result.orphaned_issues]
        assert 50 in orphan_nums
        orphan = next(o for o in result.orphaned_issues if o.number == 50)
        assert orphan.deletion_reason is not None
        assert "#100" in orphan.deletion_reason

    async def test_branch_preserved_when_parent_on_board(self):
        """A branch referencing a sub-issue whose parent IS on the board is preserved."""
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = [
            _make_branch("main"),
            _make_branch("issue-50"),
        ]

        board_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "number": 50,
                                "title": "Sub-issue",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        },
                        {
                            "content": {
                                "number": 100,
                                "title": "Parent",
                                "state": "OPEN",
                                "repository": {"nameWithOwner": "test/repo"},
                            }
                        },
                    ],
                }
            }
        }
        # #50 has parent #100 which IS on the board
        parent_resp = {
            "repository": {
                "i_50": {"parent": {"number": 100, "state": "OPEN", "title": "Parent"}},
                "i_100": None,
            }
        }

        service = _make_github_service(branches_response=branches_resp)
        service._graphql = AsyncMock(side_effect=[board_resp, parent_resp])

        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")
        result = await cleanup_service.preflight(service, "token", "testuser", request)

        preserved_names = [b.name for b in result.branches_to_preserve]
        delete_names = [b.name for b in result.branches_to_delete]
        assert "issue-50" in preserved_names
        assert "issue-50" not in delete_names

    async def test_non_solune_branch_orphaned_by_parent(self):
        """Even non-Solune branches are flagged when their referenced issue is orphaned."""
        branches_resp = MagicMock()
        branches_resp.status_code = 200
        branches_resp.json.return_value = [
            _make_branch("main"),
            _make_branch("fix/77-hotfix"),  # references #77, not on board but orphaned
        ]

        board_resp = {
            "node": {
                "items": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [],
                }
            }
        }
        parent_resp = {
            "repository": {
                "i_77": {"parent": {"number": 200, "state": "CLOSED", "title": "Gone parent"}},
            }
        }
        # issue #77 details fetch (step 6d)
        details_resp = {
            "repository": {
                "i_77": {
                    "number": 77,
                    "title": "Hotfix task",
                    "state": "OPEN",
                    "url": "https://github.com/test/repo/issues/77",
                    "labels": {"nodes": []},
                },
            }
        }

        service = _make_github_service(branches_response=branches_resp)
        service._graphql = AsyncMock(side_effect=[board_resp, parent_resp, details_resp])

        request = CleanupPreflightRequest(owner="test", repo="repo", project_id="PVT_123")
        result = await cleanup_service.preflight(service, "token", "testuser", request)

        delete_names = [b.name for b in result.branches_to_delete]
        assert "fix/77-hotfix" in delete_names
        # The orphaned issue should also appear
        orphan_nums = [o.number for o in result.orphaned_issues]
        assert 77 in orphan_nums
