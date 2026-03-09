"""Unit tests for profile store operations."""

from src.models.user import UserProfileUpdate
from src.services.profile_store import get_profile, update_avatar_path, upsert_profile


class TestGetProfile:
    async def test_returns_none_for_missing_profile(self, mock_db):
        result = await get_profile(mock_db, "missing-user")
        assert result is None


class TestUpsertProfile:
    async def test_creates_new_profile(self, mock_db):
        result = await upsert_profile(
            mock_db,
            "user1",
            UserProfileUpdate(display_name="Test User", bio="Hello world"),
        )

        assert result.github_user_id == "user1"
        assert result.display_name == "Test User"
        assert result.bio == "Hello world"
        assert result.avatar_path is None

    async def test_updates_existing_profile_and_preserves_unspecified_fields(self, mock_db):
        await upsert_profile(
            mock_db,
            "user1",
            UserProfileUpdate(display_name="Original", bio="Original bio"),
        )

        result = await upsert_profile(
            mock_db,
            "user1",
            UserProfileUpdate(display_name="Updated"),
        )

        assert result.display_name == "Updated"
        assert result.bio == "Original bio"


class TestUpdateAvatarPath:
    async def test_creates_profile_row_when_missing(self, mock_db):
        await update_avatar_path(mock_db, "user1", "avatar.png")

        result = await get_profile(mock_db, "user1")
        assert result is not None
        assert result.avatar_path == "avatar.png"

    async def test_updates_existing_profile_avatar(self, mock_db):
        await upsert_profile(
            mock_db,
            "user1",
            UserProfileUpdate(display_name="Test User", bio="Hello world"),
        )

        await update_avatar_path(mock_db, "user1", "avatar.webp")

        result = await get_profile(mock_db, "user1")
        assert result is not None
        assert result.display_name == "Test User"
        assert result.bio == "Hello world"
        assert result.avatar_path == "avatar.webp"
