"""Tests for admin authorization (US6 — FR-005).

Verifies:
- Non-admin user receives 403 on global settings PUT
- First user is auto-promoted as admin
- Admin user can modify global settings
"""

from unittest.mock import patch

import aiosqlite
from httpx import ASGITransport, AsyncClient

from src.config import Settings
from src.models.user import UserSession


def _make_session(**overrides) -> UserSession:
    defaults = {
        "github_user_id": "admin-user-001",
        "github_username": "admin-user",
        "access_token": "test-token",
    }
    defaults.update(overrides)
    return UserSession(**defaults)


def _make_settings(**overrides) -> Settings:
    defaults = {
        "github_client_id": "test-client-id",
        "github_client_secret": "test-client-secret",
        "session_secret_key": "test-session-secret-key-that-is-long-enough",
        "debug": True,
        "_env_file": None,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestAdminAuthorization:
    """Global settings PUT must be restricted to admin user."""

    async def test_non_admin_gets_403(self):
        """A non-admin user should receive 403 on PUT /settings/global."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        _make_session(
            github_user_id="admin-owner",
            github_username="admin-owner",
        )
        non_admin_session = _make_session(
            github_user_id="other-user-999",
            github_username="other-user",
        )

        settings = _make_settings()
        app = create_app()

        # Override to return non-admin session
        app.dependency_overrides[get_session_dep] = lambda: non_admin_session

        # We need a DB with admin already set
        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row
        from tests.conftest import _apply_migrations

        await _apply_migrations(db)
        # Seed global settings then set a different admin
        from src.services.database import seed_global_settings

        await seed_global_settings(db)
        # Set admin to a different user
        await db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            ("admin-owner",),
        )
        await db.commit()

        try:
            with (
                patch("src.config.get_settings", return_value=settings),
                patch("src.services.database.get_db", return_value=db),
                patch("src.services.database._connection", db),
                patch("src.api.settings.get_db", return_value=db),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.put(
                        "/api/v1/settings/global",
                        json={"ai": {"provider": "copilot"}},
                    )

            assert resp.status_code == 403, (
                f"Expected 403 for non-admin, got {resp.status_code}: {resp.text}"
            )
        finally:
            await db.close()
            app.dependency_overrides.clear()

    async def test_first_user_auto_promoted(self):
        """First authenticated user should be auto-promoted as admin."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        first_session = _make_session(
            github_user_id="first-user",
            github_username="first-user",
        )

        settings = _make_settings()
        app = create_app()
        app.dependency_overrides[get_session_dep] = lambda: first_session

        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row
        from tests.conftest import _apply_migrations

        await _apply_migrations(db)
        from src.services.database import seed_global_settings

        await seed_global_settings(db)

        try:
            with (
                patch("src.config.get_settings", return_value=settings),
                patch("src.services.database.get_db", return_value=db),
                patch("src.services.database._connection", db),
                patch("src.api.settings.get_db", return_value=db),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.put(
                        "/api/v1/settings/global",
                        json={"ai": {"provider": "copilot"}},
                    )

            # First user should be auto-promoted → request succeeds
            assert resp.status_code == 200, (
                f"Expected 200 for first user auto-promote, got {resp.status_code}: {resp.text}"
            )

            # Verify admin was persisted in DB
            cursor = await db.execute(
                "SELECT admin_github_user_id FROM global_settings WHERE id = 1"
            )
            row = await cursor.fetchone()
            admin_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]
            assert admin_id == "first-user"
        finally:
            await db.close()
            app.dependency_overrides.clear()
