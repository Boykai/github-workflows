"""Tests for project-level authorization (Finding #4 — OWASP A01).

Covers:
- verify_project_access dependency rejects unowned projects
- check_project_access standalone helper rejects unowned projects
- Authenticated request with unowned project_id returns 403
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.exceptions import AuthorizationError


class _FakeProject:
    """Lightweight stand-in for a GitHubProject with just a ``project_id``."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id


def _mock_session(username: str = "testuser") -> MagicMock:
    session = MagicMock()
    session.access_token = "ghp_test_token"
    session.github_username = username
    return session


def _mock_service(project_ids: list[str]) -> AsyncMock:
    """Return a mock GitHubProjectsService whose list_user_projects returns *project_ids*."""
    svc = AsyncMock()
    svc.list_user_projects.return_value = [_FakeProject(pid) for pid in project_ids]
    return svc


def _import_check_project_access():
    """Lazy import to avoid circular import at module level."""
    from src.dependencies import check_project_access

    return check_project_access


def _import_verify_project_access():
    """Lazy import to avoid circular import at module level."""
    from src.dependencies import verify_project_access

    return verify_project_access


# ── check_project_access (standalone) ────────────────────────────────────────


class TestCheckProjectAccess:
    async def test_allows_owned_project(self):
        check_project_access = _import_check_project_access()
        svc = _mock_service(["PVT_owned"])
        session = _mock_session()
        # Should not raise
        await check_project_access(svc, session, "PVT_owned")

    async def test_rejects_unowned_project(self):
        check_project_access = _import_check_project_access()
        svc = _mock_service(["PVT_mine"])
        session = _mock_session()
        with pytest.raises(AuthorizationError, match="do not have access"):
            await check_project_access(svc, session, "PVT_other")

    async def test_rejects_on_service_error(self):
        check_project_access = _import_check_project_access()
        svc = AsyncMock()
        svc.list_user_projects.side_effect = RuntimeError("network failure")
        session = _mock_session()
        with pytest.raises(AuthorizationError, match="Unable to verify"):
            await check_project_access(svc, session, "PVT_any")


# ── verify_project_access (FastAPI Depends wrapper) ──────────────────────────


class TestVerifyProjectAccess:
    async def test_delegates_to_check(self):
        """verify_project_access should call check_project_access under the hood."""
        verify_project_access = _import_verify_project_access()
        svc = _mock_service(["PVT_good"])
        session = _mock_session()
        request = MagicMock()
        request.app.state.github_service = svc

        # Should not raise for an owned project
        await verify_project_access(request, "PVT_good", session)

    async def test_rejects_unowned(self):
        verify_project_access = _import_verify_project_access()
        svc = _mock_service(["PVT_mine"])
        session = _mock_session()
        request = MagicMock()
        request.app.state.github_service = svc

        with pytest.raises(AuthorizationError, match="do not have access"):
            await verify_project_access(request, "PVT_theirs", session)
