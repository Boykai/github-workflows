"""Tests for profile API routes (src/api/profile.py)."""

from unittest.mock import patch

from src.api import profile as profile_api
from src.models.user import UserProfileUpdate
from src.services import profile_store


class TestGetProfile:
    async def test_returns_session_backed_profile_when_no_db_row(self, client, mock_session):
        resp = await client.get("/api/v1/users/profile")

        assert resp.status_code == 200
        data = resp.json()
        assert data["github_user_id"] == mock_session.github_user_id
        assert data["github_username"] == mock_session.github_username
        assert data["avatar_url"] == mock_session.github_avatar_url
        assert data["display_name"] is None
        assert data["bio"] is None


class TestUpdateProfile:
    async def test_patch_updates_profile_fields(self, client, mock_db):
        resp = await client.patch(
            "/api/v1/users/profile",
            json={"display_name": "  Solune User  ", "bio": "Working on profile page"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Solune User"
        assert data["bio"] == "Working on profile page"

        stored = await profile_store.get_profile(mock_db, "12345")
        assert stored is not None
        assert stored.display_name == "Solune User"

    async def test_patch_rejects_empty_display_name(self, client):
        resp = await client.patch(
            "/api/v1/users/profile",
            json={"display_name": "   "},
        )

        assert resp.status_code == 422
        assert resp.json()["error"] == "Display name cannot be empty"


class TestUploadAvatar:
    async def test_rejects_invalid_file_type(self, client, tmp_path):
        with patch("src.api.profile._get_avatar_dir", return_value=tmp_path):
            resp = await client.post(
                "/api/v1/users/profile/avatar",
                files={"file": ("avatar.gif", b"gifdata", "image/gif")},
            )

        assert resp.status_code == 422
        assert resp.json()["error"] == "Please select a PNG, JPG, or WebP image"

    async def test_rejects_oversized_file(self, client, tmp_path):
        oversized = b"x" * (5 * 1024 * 1024 + 1)
        with patch("src.api.profile._get_avatar_dir", return_value=tmp_path):
            resp = await client.post(
                "/api/v1/users/profile/avatar",
                files={"file": ("avatar.png", oversized, "image/png")},
            )

        assert resp.status_code == 413
        assert resp.json()["error"] == "Image must be smaller than 5 MB"

    async def test_uploads_avatar_and_returns_profile(self, client, mock_db, tmp_path):
        with patch("src.api.profile._get_avatar_dir", return_value=tmp_path):
            resp = await client.post(
                "/api/v1/users/profile/avatar",
                files={"file": ("avatar.png", b"pngdata", "image/png")},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["avatar_url"] is not None
        assert data["avatar_url"].startswith("/api/v1/users/profile/avatar/")

        stored = await profile_store.get_profile(mock_db, "12345")
        assert stored is not None
        assert stored.avatar_path is not None
        assert (tmp_path / stored.avatar_path).exists()


class TestGetAvatar:
    async def test_rejects_invalid_filename(self, client, tmp_path):
        with patch("src.api.profile._get_avatar_dir", return_value=tmp_path):
            resp = await client.get("/api/v1/users/profile/avatar/not-a-valid-avatar.png")

        assert resp.status_code == 400
        assert resp.json()["error"] == "Invalid filename"

    def test_resolver_rejects_path_traversal(self, tmp_path):
        with patch("src.api.profile._get_avatar_dir", return_value=tmp_path):
            assert profile_api._resolve_avatar_path("../../secret.png") is None

    async def test_serves_uploaded_avatar(self, client, mock_db, tmp_path):
        avatar_name = "deadbeef_avatar.png"
        avatar_path = tmp_path / avatar_name
        avatar_path.write_bytes(b"pngdata")
        await profile_store.upsert_profile(mock_db, "12345", UserProfileUpdate(display_name="User"))
        await profile_store.update_avatar_path(mock_db, "12345", avatar_name)

        with patch("src.api.profile._get_avatar_dir", return_value=tmp_path):
            resp = await client.get(f"/api/v1/users/profile/avatar/{avatar_name}")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content == b"pngdata"
