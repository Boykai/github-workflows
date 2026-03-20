from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.exceptions import AppException, AuthorizationError, ValidationError
from src.models.user import UserSession


def _request_with_state(**attrs):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**attrs)))


def _session(**overrides) -> UserSession:
    defaults = {
        "github_user_id": "12345",
        "github_username": "octocat",
        "access_token": "gho_test_token",
        "selected_project_id": "PVT_123",
    }
    defaults.update(overrides)
    return UserSession(**defaults)


class TestServiceGetters:
    def test_get_github_service_prefers_app_state(self):
        from src.dependencies import get_github_service

        service = object()
        request = _request_with_state(github_service=service)

        assert get_github_service(request) is service

    def test_get_github_service_falls_back_to_global(self):
        from src.dependencies import get_github_service

        request = _request_with_state()
        fallback = object()

        with patch("src.services.github_projects.github_projects_service", fallback):
            assert get_github_service(request) is fallback

    def test_get_connection_manager_prefers_app_state(self):
        from src.dependencies import get_connection_manager

        manager = object()
        request = _request_with_state(connection_manager=manager)

        assert get_connection_manager(request) is manager

    def test_get_connection_manager_falls_back_to_global(self):
        from src.dependencies import get_connection_manager

        request = _request_with_state()
        fallback = object()

        with patch("src.services.websocket.connection_manager", fallback):
            assert get_connection_manager(request) is fallback

    def test_get_database_prefers_app_state(self):
        from src.dependencies import get_database

        db = object()
        request = _request_with_state(db=db)

        assert get_database(request) is db

    def test_get_database_falls_back_to_global(self):
        from src.dependencies import get_database

        request = _request_with_state()
        db = object()

        with patch("src.services.database.get_db", return_value=db):
            assert get_database(request) is db

    def test_get_session_dep_lazy_import_matches_auth_alias(self):
        from src.api.auth import get_session_dep as auth_get_session_dep
        from src.dependencies import _get_session_dep

        assert _get_session_dep() is auth_get_session_dep


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_require_admin_errors_when_global_settings_row_missing(self):
        from src.dependencies import require_admin

        cursor = AsyncMock()
        cursor.fetchone.return_value = None

        db = AsyncMock()
        db.execute.return_value = cursor

        with patch("src.dependencies.get_database", return_value=db):
            with pytest.raises(AppException, match="admin settings are missing") as exc_info:
                await require_admin(_request_with_state(), _session())

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_require_admin_seeds_configured_admin_user(self):
        from src.dependencies import require_admin

        cursor = AsyncMock()
        cursor.fetchone.return_value = {"admin_github_user_id": None}

        db = AsyncMock()
        db.execute.side_effect = [cursor, AsyncMock()]

        settings = SimpleNamespace(admin_github_user_id="12345", debug=False)

        with (
            patch("src.dependencies.get_database", return_value=db),
            patch("src.config.get_settings", return_value=settings),
        ):
            session = await require_admin(_request_with_state(), _session())

        assert session.github_user_id == "12345"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_require_admin_auto_promotes_first_debug_user(self):
        from src.dependencies import require_admin

        select_cursor = AsyncMock()
        select_cursor.fetchone.side_effect = [
            {"admin_github_user_id": None},
            {"admin_github_user_id": "12345"},
        ]
        update_cursor = AsyncMock()
        update_cursor.rowcount = 1

        db = AsyncMock()
        db.execute.side_effect = [select_cursor, update_cursor, select_cursor]

        settings = SimpleNamespace(admin_github_user_id=None, debug=True)

        @asynccontextmanager
        async def _txn(_db):
            yield

        with (
            patch("src.dependencies.get_database", return_value=db),
            patch("src.config.get_settings", return_value=settings),
            patch("src.services.chat_store.transaction", _txn),
        ):
            session = await require_admin(_request_with_state(), _session())

        assert session.github_user_id == "12345"

    @pytest.mark.asyncio
    async def test_require_admin_rejects_production_without_configured_admin(self):
        from src.dependencies import require_admin

        cursor = AsyncMock()
        cursor.fetchone.return_value = {"admin_github_user_id": None}

        db = AsyncMock()
        db.execute.return_value = cursor

        settings = SimpleNamespace(admin_github_user_id=None, debug=False)

        with (
            patch("src.dependencies.get_database", return_value=db),
            patch("src.config.get_settings", return_value=settings),
        ):
            with pytest.raises(AppException, match="ADMIN_GITHUB_USER_ID must be set") as exc_info:
                await require_admin(_request_with_state(), _session())

        assert exc_info.value.status_code == 500


class TestVerifyProjectAccess:
    @pytest.mark.asyncio
    async def test_verify_project_access_allows_owned_project(self):
        from src.dependencies import verify_project_access

        svc = AsyncMock()
        svc.list_user_projects.return_value = [SimpleNamespace(project_id="PVT_123")]

        with patch("src.dependencies.get_github_service", return_value=svc):
            await verify_project_access(_request_with_state(), "PVT_123", _session())

    @pytest.mark.asyncio
    async def test_verify_project_access_rejects_unknown_project(self):
        from src.dependencies import verify_project_access

        svc = AsyncMock()
        svc.list_user_projects.return_value = [SimpleNamespace(project_id="PVT_other")]

        with patch("src.dependencies.get_github_service", return_value=svc):
            with pytest.raises(AuthorizationError, match="do not have access"):
                await verify_project_access(_request_with_state(), "PVT_123", _session())

    @pytest.mark.asyncio
    async def test_verify_project_access_maps_service_errors(self):
        from src.dependencies import verify_project_access

        svc = AsyncMock()
        svc.list_user_projects.side_effect = RuntimeError("GitHub unavailable")

        with patch("src.dependencies.get_github_service", return_value=svc):
            with pytest.raises(AuthorizationError, match="Unable to verify project access"):
                await verify_project_access(_request_with_state(), "PVT_123", _session())


class TestRequireSelectedProject:
    def test_require_selected_project_returns_selected_value(self):
        from src.dependencies import require_selected_project

        assert require_selected_project(_session(selected_project_id="PVT_456")) == "PVT_456"

    def test_require_selected_project_raises_without_selection(self):
        from src.dependencies import require_selected_project

        with pytest.raises(ValidationError, match="No project selected"):
            require_selected_project(_session(selected_project_id=None))
